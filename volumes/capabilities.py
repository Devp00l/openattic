# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; replace-tabs on;

"""
 *  Copyright (C) 2011-2012, it-novum GmbH <community@open-attic.org>
 *
 *  openATTIC is free software; you can redistribute it and/or modify it
 *  under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; version 2.
 *
 *  This package is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
"""

import operator

class AbstractCapabilityNode(object):
    op = None

    def __init__(self, lft, rgt):
        self.lft = lft
        self.rgt = rgt

    def __add__(self, other):
        return CapabilityAddNode(self, other)

    def __mul__(self, other):
        return CapabilityMulNode(self, other)

    def eval_(self, devicecaps):
        satisfied = {}

        def _get(something):
            """ Something might be True, a Capability*Node, or a Capability.
                Devicecaps is a list of capabilities that some device provides.

                Translate it to a number, in the context of devicecaps.
            """
            if something is True:
                return True
            elif isinstance(something, AbstractCapabilityNode):
                points, child_satisfied = something.eval_(devicecaps)
                satisfied.update(child_satisfied)
                return points
            elif issubclass(something, Capability):
                # check if we have a devicecap that satisfies our dependency on "something".
                # that is the case if we either have "something" directly, or a subclass
                # of it, because subclasses satisfy dependencies to their base classes.
                # btw: subclass(something, something) is True, so no need to check for
                # "something" explicitly.
                for devcap in devicecaps:
                    if issubclass(devcap, something):
                        satisfied[something] = True
                        return True
                satisfied[something] = False
                return False
            else:
                return TypeError("Unexpected type '%r'" % something)

        return self.op( _get(self.lft), _get(self.rgt) ), satisfied


class CapabilityAddNode(AbstractCapabilityNode):
    op = operator.add

class CapabilityMulNode(AbstractCapabilityNode):
    op = operator.mul


class CapabilityMeta(type):
    capabilities = []

    def __init__( cls, name, bases, attrs ):
        type.__init__( cls, name, bases, attrs )
        if name != "Capability":
            CapabilityMeta.capabilities.append(cls)

    def __add__(self, other):
        return CapabilityAddNode(self, other)

    def __radd__(self, other):
        return CapabilityAddNode(other, self)

    def __mul__(self, other):
        return CapabilityMulNode(self, other)

    def __rmul__(self, other):
        return CapabilityMulNode(other, self)

class Capability(object):
    __metaclass__ = CapabilityMeta
    # The ``flag'' class variable carries a bit flag used to represent a capability in an int.
    # It should be hardcoded explicitly instead of being implicitly derived from somewhere,
    # because if this flag should change for some reason, all hell will break loose.
    flag = None

class SlowSATASpeedCapability(Capability):
    """ 3.5" 7200RPM SATA disks """
    flag = (1<<0)

class FastSATASpeedCapability(SlowSATASpeedCapability):
    """ 2.5" 10kRPM SATA disks """
    flag = (1<<1)

class SlowSASSpeedCapability(FastSATASpeedCapability):
    """ 2.5" 10kRPM SAS Disks """
    flag = (1<<2)

class FastSASSpeedCapability(SlowSASSpeedCapability):
    """ 2.5" 15kRPM SAS Disks """
    flag = (1<<3)

class SSDSpeedCapability(FastSASSpeedCapability):
    """ SSDs """
    flag = (1<<4)

class UnlimitedWritesCapability(Capability):
    """ Does not age when written to (i.e., unlike SSDs). """
    flag = (1<<5)


class BlockbasedCapability(Capability):
    """ Block-based access e.g. over iSCSI or FC """
    flag = (1<<6)

class FailureToleranceCapability(Capability):
    flag = (1<<7)

class MirroredBlockDeviceCapability(BlockbasedCapability):
    """ Mirrored block device like DRBD or RBD """
    flag = (1<<8)

class MultiPrimaryBlockDeviceCapability(BlockbasedCapability):
    """ Dual-Primary DRBD, RBD """
    flag = (1<<9)

class FileIOCapability(BlockbasedCapability):
    flag = (1<<10)

class BlockIOCapability(BlockbasedCapability):
    flag = (1<<11)


class FilesystemCapability(Capability):
    """ File-based access e.g. over NFS or Samba """
    flag = (1<<12)

class MirroredFilesystemCapability(FilesystemCapability):
    """ Mirrored file-systems like Ceph """
    flag = (1<<13)

class MultiPrimaryFilesystemCapability(FilesystemCapability):
    """ Mirrored file-systems like Ceph, that are writable on more than one host """
    flag = (1<<14)

class VolumeSnapshotCapability(Capability):
    """ Supports snapshots for the entire volume """
    flag = (1<<15)

class SubvolumesCapability(Capability):
    """ Supports subvolumes """
    flag = (1<<16)

class SubvolumeSnapshotCapability(SubvolumesCapability):
    """ Supports snapshots for subvolumes """
    flag = (1<<17)

class FileSnapshotCapability(FilesystemCapability):
    """ Supports snapshots which can be mounted to restore individual files """
    flag = (1<<18)

class PosixACLCapability(FilesystemCapability):
    """ Supports snapshots which can be mounted to restore individual files """
    flag = (1<<19)

class DeduplicationCapability(FilesystemCapability):
    """ Supports deduplication """
    flag = (1<<19)

class CompressionCapability(FilesystemCapability):
    """ Supports compression """
    flag = (1<<20)

class GrowCapability(Capability):
    """ Supports growing """
    flag = (1<<21)

class ShrinkCapability(Capability):
    """ Supports shrinking """
    flag = (1<<22)

class ParallelIOCapability(FilesystemCapability):
    """ Filesystem is optimized for efficiently handling massively parallel IO. """
    flag = (1<<23)

class SectorBlocksCapability(FilesystemCapability):
    """ File system blocksize == sector size (512 Bytes). """
    flag = (1<<24)

def to_flags(capabilities):
    return reduce(operator.or_, [cap.flag for cap in capabilities])

def from_flags(flags):
    return [ cap for cap in CapabilityMeta.capabilities if cap.flag & flags == cap.flag ]


class Profile(object):
    capabilities = None

class FileserverProfile(Profile):
    """ Optimized for a file server """
    capabilities = FilesystemCapability * (VolumeSnapshotCapability + PosixACLCapability) * (True + GrowCapability + ShrinkCapability + DeduplicationCapability + CompressionCapability)

class VMProfile(Profile):
    """ Optimized for running VMs that support proper disk alignment """
    capabilities = SlowSASSpeedCapability * ParallelIOCapability * (True + GrowCapability + ShrinkCapability + DeduplicationCapability + CompressionCapability)

class LegacyVMProfile(VMProfile):
    """ Optimized for running VMs that don't support disk alignment """
    capabilities = VMProfile.capabilities * SectorBlocksCapability


class Device(object):
    """ Describes some kind of device, regarding its capabilities.

        ``requires'': Either another device class, or a list of capabilities
                      required for this device to be set up properly.
        ``provides'': List of capabilities provided by **this** device (be
                      careful not to name capabilities of the parents here).
        ``removes'':  List of capabilities that parent devices have, but the
                      resulting device does not.
                      E.g.: File systems are installed on a block device, but
                      do not provide block devices themselves.
    """
    requires = None
    provides = None
    removes  = None

    def __init__(self):
        # Make sure each instance gets its own lists.
        if self.requires is None:
            self.requires = []
        elif isinstance(self.__class__.requires, list):
            self.requires = [cap for cap in self.__class__.requires]
        if self.provides is None:
            self.provides = []
        else:
            self.provides = [cap for cap in self.__class__.provides]
        if self.removes  is None:
            self.removes  = []
        else:
            self.removes  = [cap for cap in self.__class__.removes ]

class Disk(Device):
    provides = [
        BlockbasedCapability,
        BlockIOCapability,
        ]

class Raid5(Device):
    requires = [
        BlockbasedCapability,
        ]
    provides = [
        FailureToleranceCapability,
        ]

class VolumeGroup(Device):
    requires = [
        BlockbasedCapability,
        FailureToleranceCapability,
        ]
    provides = [
        SubvolumesCapability,
        SubvolumeSnapshotCapability,
        ]

class LogicalVolume(Device):
    requires = VolumeGroup
    provides = [
        GrowCapability,
        ShrinkCapability,
        ]
    removes  = [
        SubvolumesCapability,
        SubvolumeSnapshotCapability,
        ]

class ExtFS(Device):
    requires = [
        BlockbasedCapability,
        FailureToleranceCapability,
        ]
    provides = [
        FilesystemCapability,
        PosixACLCapability,
        GrowCapability,
        ShrinkCapability,
        FileIOCapability,
        ]
    removes  = [
        BlockbasedCapability,
        BlockIOCapability,
        ]

class XfsDefaultBlocks(Device):
    requires = [
        BlockbasedCapability,
        FailureToleranceCapability,
        ]
    provides = [
        FilesystemCapability,
        PosixACLCapability,
        GrowCapability,
        ParallelIOCapability,
        FileIOCapability,
        ]
    removes  = [
        BlockbasedCapability,
        BlockIOCapability,
        ]

class XfsSectorBlocks(Device):
    requires = XfsDefaultBlocks.requires
    provides = XfsDefaultBlocks.provides + [SectorBlocksCapability]
    removes  = XfsDefaultBlocks.removes

class Zpool(Device):
    requires = [
        BlockbasedCapability,
        ]
    provides = [
        FailureToleranceCapability,
        FilesystemCapability,
        VolumeSnapshotCapability,
        SubvolumesCapability,
        SubvolumeSnapshotCapability,
        FileSnapshotCapability,
        GrowCapability,
        ShrinkCapability,
        DeduplicationCapability,
        CompressionCapability,
        FileIOCapability,
        ]
    removes  = [
        BlockbasedCapability,
        BlockIOCapability,
        ]

class Zfs(Device):
    requires = Zpool

class Btrfs(Device):
    requires = [
        BlockbasedCapability,
        FailureToleranceCapability,
        ]
    provides = [
        FilesystemCapability,
        VolumeSnapshotCapability,
        SubvolumesCapability,
        SubvolumeSnapshotCapability,
        FileSnapshotCapability,
        GrowCapability,
        ShrinkCapability,
        DeduplicationCapability,
        CompressionCapability,
        PosixACLCapability,
        FileIOCapability,
        ]
    removes  = [
        BlockbasedCapability,
        BlockIOCapability,
        ]

class BtrfsSubvolume(Device):
    requires = Btrfs

class DrbdConnection(Device):
    requires = [
        FailureToleranceCapability,
        ]
    provides = [
        MirroredBlockDeviceCapability,
        ]

class ImageFile(Device):
    requires = [
        FilesystemCapability,
        ]
    provides = [
        BlockbasedCapability,
        ]
    removes  = [
        FilesystemCapability,
        ]


class RequirementNotSatisfied(Exception):
    pass

def device_stack_capabilities(devs, topdev=None):
    """ When given a stack of devices, returns a single device that expresses
        the requirements and capabilities of the whole stack.
    """
    if not devs:
        # the stack is complete.
        return topdev

    if topdev is None:
        return device_stack_capabilities(devs[1:], devs[0])

    nextdev = devs[0]
    if not isinstance(nextdev, Device):
        raise TypeError("need device *instances*, not classes")

    # check if we can actually build this stack.
    # this will fail if:
    # a) nextdev requires topdev to be a certain device, and topdev is the wrong one;
    # b) nextdev requires some capability that topdev does not provide.
    if not isinstance(nextdev.requires, list):
        if nextdev.requires != type(topdev):
            raise RequirementNotSatisfied("'%r' requires '%r', got '%r' instead" % (nextdev, nextdev.requires, topdev))
    else:
        for dependency in nextdev.requires:
            if dependency not in topdev.provides:
                raise RequirementNotSatisfied("'%r' requires '%r'" % (nextdev, dependency))

    # the dependencies of the complete stack are equal to the depends of the lowest
    # device, so carry them on
    nextdev.requires = [cap for cap in topdev.requires]

    # merge provides: the top of the stack will provide everything that the current
    # top device has to offer + everything it adheres itself...
    for capability in topdev.provides:
        if capability not in nextdev.provides:
            nextdev.provides.append(capability)

    # ...except for a couple of capabilities that are removed by the next component.
    removecaps = []
    for capability in nextdev.removes:
        print "checking", capability
        if capability in nextdev.provides:
            print "removing", capability
            nextdev.provides.remove(capability)
        # the stack can only remove stuff that it actually requires, so if that is
        # NOT the case, remove it from removes as well.
        # sadly we can't do that *right* now, because that borks the iteration.
        if capability not in topdev.requires:
            removecaps.append(capability)

    for capability in removecaps:
        nextdev.removes.remove(capability)

    # now see what happens when we put another device on top of our stack.
    return device_stack_capabilities(devs[1:], nextdev)

def testdis():
    return device_stack_capabilities([
        Disk(), Raid5(), VolumeGroup(), LogicalVolume(), XfsDefaultBlocks()
        ])
