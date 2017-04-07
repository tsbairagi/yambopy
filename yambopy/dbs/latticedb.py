# Copyright (c) 2015, Henrique Miranda
# All rights reserved.
#
# This file is part of the yambopy project
#
from yambopy import *
from netCDF4 import Dataset
import itertools
import operator

atol = 1e-6

def vec_in_list(veca,vec_list):
    """ check if a vector exists in a list of vectors
    """
    return np.array([ np.allclose(veca,vecb,rtol=atol,atol=atol) for vecb in vec_list ]).any()

def red_car(red,lat):
    """
    Convert reduced coordinates to cartesian
    """
    return np.array(map( lambda coord: coord[0]*lat[0]+coord[1]*lat[1]+coord[2]*lat[2], red))

def car_red(car,lat):
    """
    Convert cartesian coordinates to reduced
    """
    return np.array(map( lambda coord: np.linalg.solve(np.array(lat).T,coord), car))

def rec_lat(lat):
    """
    Calculate the reciprocal lattice vectors
    """
    a1,a2,a3 = np.array(lat)
    v = np.dot(a1,np.cross(a2,a3))
    b1 = np.cross(a2,a3)/v
    b2 = np.cross(a3,a1)/v
    b3 = np.cross(a1,a2)/v
    return np.array([b1,b2,b3])

class YamboLatticeDB():
    def __init__(self, save='SAVE',filename='ns.db1',expand=True):
        self.filename = '%s/%s'%(save,filename)
        self.readDB()
        # generate additional structure using the data read from the DBs
        self.process()
        if expand: self.expandKpoints()
            
    def readDB(self):
        """
        Read the lattice information from the netcdf file
        """
        try:
            database = Dataset(self.filename)
        except:
            print "error opening %s in YamboLatticeDB"%self.filename
            exit()

        self.lat         = database.variables['LATTICE_VECTORS'][:].T
        self.alat        = database.variables['LATTICE_PARAMETER'][:].T
        natoms           = database.variables['N_ATOMS'][:].astype(int).T
        self.atomic_numbers   = database.variables['atomic_numbers'][:].astype(int)
        self.atomic_positions = database.variables['ATOM_POS'][0,:]
        self.sym_car     = database.variables['SYMMETRY'][:]
        self.iku_kpoints = database.variables['K-POINTS'][:].T
        dimensions = database.variables['DIMENSIONS'][:]
        self.temperature = dimensions[13]
        self.nelectrons = dimensions[14]
        self.nkpoints  = int(dimensions[6])
        self.spin = int(dimensions[11])
        self.time_rev = dimensions[9]
        #atomic numbers
        atomic_numbers = [[self.atomic_numbers[n]]*na for n,na in enumerate(natoms)]
        self.atomic_numbers = list(itertools.chain.from_iterable(atomic_numbers))
        #atomic masses
        self.atomic_masses = [atomic_mass[a] for a in self.atomic_numbers]

        database.close()
        
    def process(self):
        inv = np.linalg.inv
        #caclulate the reciprocal lattice
        self.rlat  = rec_lat(self.lat)
        self.nsym  = len(self.sym_car)
        
        #convert form internal yambo units to cartesian lattice units
        self.car_kpoints = np.array([ k/self.alat for k in self.iku_kpoints ])
        self.red_kpoints = car_red(self.car_kpoints,self.rlat)
        self.nkpoints = len(self.car_kpoints)
        
        #convert cartesian transformations to reciprocal transformations
        self.sym_rec = np.zeros([self.nsym,3,3])
        for n,s in enumerate(self.sym_car):
            self.sym_rec[n] = inv(s).T
            
        #get a list of symmetries with time reversal
        nsym = len(self.sym_car)
        self.time_rev_list = [False]*nsym
        for i in xrange(nsym):
            self.time_rev_list[i] = ( i >= nsym/(self.time_rev+1) )
        
    def expandKpoints(self):
        """
        Take a list of qpoints and symmetry operations and return the full brillouin zone
        with the corresponding index in the irreducible brillouin zone
        """

        #check if the kpoints were already exapnded
        kpoints_indexes  = []
        kpoints_full     = []
        symmetry_indexes = []

        #kpoints in the full brillouin zone organized per index
        kpoints_full_i = {}

        #expand using symmetries
        for nk,k in enumerate(self.car_kpoints):
            #if the index in not in the dicitonary add a list
            if nk not in kpoints_full_i:
                kpoints_full_i[nk] = []
                    
            for ns,sym in enumerate(self.sym_car):
                
                new_k = np.dot(sym,k)

                #check if the point is inside the bounds
                k_red = car_red([new_k],self.rlat)[0]
                k_bz = (k_red+atol)%1
                
                #if the vector is not in the list of this index add it
                if not vec_in_list(k_bz,kpoints_full_i[nk]):
                    kpoints_full_i[nk].append(k_bz)
                    kpoints_full.append(new_k)
                    kpoints_indexes.append(nk)
                    symmetry_indexes.append(ns)
                    continue

        #calculate the weights of each of the kpoints in the irreducible brillouin zone
        self.full_nkpoints = len(kpoints_full)
        weights = np.zeros([self.nkpoints])
        for nk in kpoints_full_i:
            weights[nk] = float(len(kpoints_full_i[nk]))/self.full_nkpoints

        print "%d kpoints expanded to %d"%(len(self.car_kpoints),len(kpoints_full))

        #set the variables
        self.weights_ibz      = np.array(weights)
        self.car_kpoints      = np.array(kpoints_full)
        self.red_kpoints      = car_red(self.car_kpoints,self.rlat)
        self.kpoints_indexes  = np.array(kpoints_indexes)
        self.symmetry_indexes = np.array(symmetry_indexes)