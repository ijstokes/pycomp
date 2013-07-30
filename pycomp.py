#!/usr/bin/env python

import os
import sys
import glob

from os.path import join as join
from os.path import basename as basename

locations = [   ('conda', 'pkgs', '*'),
                ('bin', 'bin', '*'),
                ('psl_mod', 'lib', 'python?.?', '*.py'),
                ('psl_pkg', 'lib', 'python?.?', None),
                ('site_mod', 'lib', 'python?.?', 'site-packages', '*.py'),
                ('site_pkg', 'lib', 'python?.?', 'site-packages', None),
            ]

def usage():
    sys.stderr.write("Compare one or more python distributions to a reference distribution\n\n")
    sys.stderr.write("\tusage: %s /path/to/pyref /path/to/pycomp1 [/path/to/pycomp2 ...]\n\n" % sys.argv[0])
    sys.stderr.write("\te.g.: %s /opt/python ~/python /usr/lib\n" % sys.argv[0])
    sys.exit(-1)

def compare(da,db):
    for dist in [da,db]:
        if not os.path.exists(dist):
            raise IOError('Python distribution directory not found: %s' % dist)

    result = {}
    result['diff']      = {da: {},    db: {}}
    result['missing']   = {da: set(), db: set()}

    for loc in locations:
        name = loc[0]
        path = join(loc[1:-1])
        if loc[-1] == None:
            dira = glob.iglob(join(da,*loc[1:-1]))
            dirb = glob.iglob(join(db,*loc[1:-1]))
            a = set([basename(d) for d in child_dirs(dira.next())])
            b = set([basename(d) for d in child_dirs(dirb.next())])
        else:
            a = set((basename(f) for f in glob.iglob(join(da,*loc[1:]))))
            b = set((basename(f) for f in glob.iglob(join(db,*loc[1:]))))

        result['diff'][da][name] = sorted(a - b)
        result['diff'][db][name] = sorted(b - a)
        result['missing'][db].update(set([guess(p) for p in result['diff'][da][name]]))
        result['missing'][da].update(set([guess(p) for p in result['diff'][db][name]]))

    for s in (result['missing'][da], result['missing'][db]):
        if 'python' in s:
            s.remove('python')

    return result

def compare_n(*dists):
    if len(dists) < 2:
        raise ValueError('Two or more directory paths required to compare')

    results = {}
    results['ref_missing'] = set()
    ref = dists[0]

    for comp in dists[1:]:
        print "results[(%s,%s)]" % (ref, comp)
        results[(ref, comp)] = compare(ref, comp)
        results['ref_missing'].update(results[(ref, comp)]['missing'][ref])

    return results

def main():
    if len(sys.argv) < 3:
        usage()

    dists = []
    for a in sys.argv[1:]:
        dists.append(os.path.expanduser(os.path.expandvars(a)))

    results = compare_n(*dists)

    print "=" * 60
    ref = dists[0]
    for comp in dists[1:]:
        print "%s vs %s" % (ref, comp)
        print "=" * 60
        result = results[(ref,comp)]
        for loc in locations:
            name = loc[0]
            print name, "=" * (59 - len(name))
            if result['diff'][ref][name]:
                print "\tjust in %s:" % ref
                for p in result['diff'][ref][name]:
                    print "\t\t", p
            if result['diff'][comp][name]:
                print "\tjust in %s:" % comp
                for p in result['diff'][name][comp]:
                    print "\t\t", p
        print "=" * 60
        for inst  in (ref, comp):
            if result['missing'][inst]:
                print "missing from %s: (best guess of package name)" % inst
                print "\t", " ".join(result['missing'][inst])

def child_dirs(dir):
    """ Thanks to Stackoverflow for this one:
    http://stackoverflow.com/questions/800197/get-all-of-the-immediate-subdirectories-in-python
    """
    return [name for name in os.listdir(dir)
            if os.path.isdir(os.path.join(dir, name))]

def guess(p):
    dash  = p.find('-')
    point = p.find('.')
    if dash == -1:
        dash = 1e4
    if point == -1:
        point = 1e4
    return p[:min(len(p),dash,point)]

if __name__ == '__main__':
    main()
