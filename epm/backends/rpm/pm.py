from epm.backends.rpm import RPMPackage
from epm.pm import PackageManager
from epm.transaction import *
from epm import *

import sys, os
import rpm

class RPMPackageManager(PackageManager):

    def commit(self, trans):
        set = trans.getChangeSet().getSet()

        # Build obsoletes relations.
        obsoleting = {}
        obsoleted = {}
        for pkg in set:
            if not isinstance(pkg, RPMPackage):
                continue
            for prv in pkg.provides:
                for obs in prv.obsoletedby:
                    for obspkg in obs.packages:
                        if set.get(obspkg) is INSTALL:
                            obsoleted[pkg] = True
                            obsoleting[obspkg] = True

        ts = rpm.ts()
        packagesTotal = 0
        for pkg in set:
            if not isinstance(pkg, RPMPackage):
                continue
            op = set[pkg]
            if op is INSTALL:
                loader = [x for x in pkg.loaderinfo if not x.getInstalled()][0]
                info = loader.getInfo(pkg)
                mode = pkg in obsoleting and "u" or "i"
                url = info.getURL()
                if not url.startswith("file://"):
                    raise Error, "Ooops.. not yet supported."
                fd = os.open(url[7:], os.O_RDONLY)
                h = ts.hdrFromFdno(fd)
                os.close(fd)
                ts.addInstall(h, info, mode)
                packagesTotal += 1
            elif pkg not in obsoleted:
                version = pkg.version
                if ":" in version:
                    version = version[version.find(":")+1:]
                ts.addErase("%s-%s" % (pkg.name, version))
        ts.order()
        cb = RPMStandardCallback(packagesTotal)
        ts.run(cb, None)


class RPMStandardCallback:
    def __init__(self, packagesTotal):
        self.hashesPrinted = 0
        self.packagesTotal = packagesTotal
        self.progressTotal = 0
        self.progressCurrent = 0
        self.fd = None

    def __call__(self, what, amount, total, info, data):

        if what == rpm.RPMCALLBACK_INST_OPEN_FILE:
            url = info.getURL()
            if not url.startswith("file://"):
                raise Error, "Ooops.. not yet supported."
            filename = url[7:]
            self.fd = os.open(filename, os.O_RDONLY)
            return self.fd
        
        elif what == rpm.RPMCALLBACK_INST_CLOSE_FILE:
            if self.fd is not None:
                os.close(self.fd)
                self.fd = None

        elif what == rpm.RPMCALLBACK_INST_START:
            self.hashesPrinted = 0
            name = info.getPackage().name
            if sys.stdout.isatty():
                sys.stdout.write("%4d:%-23.23s" %
                                 (self.progressCurrent+1, name))
            else:
                sys.stdout.write("%-28.28s" % name)
            sys.stdout.flush()

        elif (what == rpm.RPMCALLBACK_TRANS_PROGRESS or
              what == rpm.RPMCALLBACK_INST_PROGRESS):
            self.printHash(amount, total)
            sys.stdout.flush()

        elif what == rpm.RPMCALLBACK_TRANS_START:
            self.hashesPrinted = 0
            self.progressTotal = 1
            self.progressCurrent = 0
            sys.stdout.write("%-28s" % "Preparing...")
            sys.stdout.flush()

        elif what == rpm.RPMCALLBACK_TRANS_STOP:
            self.printHash(1, 1)
            self.progressTotal = self.packagesTotal
            self.progressCurrent = 0

    def printHash(self, amount, total):
        hashesNeeded = 0
        hashesTotal = 50
        if sys.stdout.isatty():
            hashesTotal = 44

        if self.hashesPrinted != hashesTotal:
            if total:
                hashesNeeded = int(hashesTotal*(float(amount)/total))
            else:
                hashesNeeded = hashesTotal
            while hashesNeeded > self.hashesPrinted:
                if sys.stdout.isatty():
                    sys.stdout.write("#"*self.hashesPrinted)
                    sys.stdout.write(" "*(hashesTotal-self.hashesPrinted))
                    if total:
                        percent = 100 * float(amount)/total
                    else:
                        percent = 100
                    sys.stdout.write("(%3d%%)" % percent)
                    sys.stdout.write("\b"*(hashesTotal+6))
                else:
                    sys.stdout.write("#")
                self.hashesPrinted += 1
            sys.stdout.flush()
            self.hashesPrinted = hashesNeeded
            if self.hashesPrinted == hashesTotal:
                self.progressCurrent += 1
                if sys.stdout.isatty():
                    sys.stdout.write("#"*(self.hashesPrinted-1))
                    if self.progressTotal:
                        percent = 100 * float(self.progressCurrent)/ \
                                        self.progressTotal
                    else:
                        percent = 100
                    sys.stdout.write(" [%3d%%]" % percent)
                sys.stdout.write("\n")
            sys.stdout.flush()
