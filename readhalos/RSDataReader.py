import numpy as np
import readParentsList as rp
import pandas
import struct
import os
import sys
import readsnapshots.readsnapHDF5_greg as rsg

import asciitable
def load_rsboundindex(hpath,snap):
    return asciitable.read(hpath+'/halos/halos_'+str(snap)+'/iterboundindex.csv',names=['hid','numbound','numtot','loc','numiter'])

class RSDataReader:
    """
    Alex's 10/4/13 rewrite of RSDataReader, combining v2 and v3 and cleaning everything up
    """
    def __init__(self, dir, snap_num, version=2, sort_by='mgrav', base='halos_', digits=2, noparents=False, AllParticles=False, unboundfrac=None, minboundpart=None):
        self.dir = dir
        self.snap_num = snap_num
        self.base = base
        self.AllParticles = AllParticles
        self.version=version
        self.sort_by = sort_by

        self.particlebytes = 8

        if minboundpart != None:
            self.boundindexpath = dir+'/'+base+str(snap_num).zfill(digits)+'/iterboundindex.csv'
            self.boundpartspath = dir+'/'+base+str(snap_num).zfill(digits)+'/iterboundparts.dat'
            assert os.path.exists(self.boundindexpath)
            assert os.path.exists(self.boundpartspath)

        def getfilename(file_num):
            if version==10:
                return dir+'/'+base+str(snap_num).zfill(digits)+'/'+base+str(snap_num).zfill(digits)+'.'+str(file_num)+'.boundbin'
            elif version==7 or version == 8:
                return dir+'/'+base+str(snap_num).zfill(digits)+'/'+base+str(snap_num).zfill(digits)+'.'+str(file_num)+'.fullbin'
            return dir+'/'+base+str(snap_num).zfill(digits)+'/'+base+str(snap_num).zfill(digits)+'.'+str(file_num)+'.bin'

        if version==10:
            self.num_p ='num_bound'
        elif version==7 or version == 8:
            self.num_p = 'total_npart'
        else:
            self.num_p = 'npart'

        numheaderbytes=256
        if version==1:
            print "VERSION 1 (Greg's cosmboxes version) NOT IMPLEMENTED!"
            datatypesstr = ""
            numbytes = 256
            raise Exception("Not implemented error")
        if version==2: #RC1
            headerfmt = "qqqffffffffffqqffq"+"x"*(256-96)
            varlist = np.dtype([('id','<i8'),\
                                ('posX','<f8'),('posY','<f8'),('posZ','<f8'),\
                                ('pecVX','<f8'),('pecVY','<f8'),('pecVZ','<f8'),\
                                ('corevelx','<f8'),('corevely','<f8'),('corevelz','<f8'),\
                                ('bulkvelx','<f8'),('bulkvely','<f8'),('bulkvelz','<f8'),\
                                ('mvir','<f8'),('rvir','<f8'),('child_r','<f8'),('vmax_r','<f8'),\
                                ('mgrav','<f8'),('vmax','<f8'),('rvmax','<f8'),('rs','<f8'),('rs_klypin','<f8'),\
                                ('vrms','<f8'),('Jx','<f8'),('Jy','<f8'),('Jz','<f8'),\
                                ('Epot','<f8'),('spin','<f8'),('altm1','<f8'),('altm2','<f8'),('altm3','<f8'),('altm4','<f8'),\
                                ('Xoff','<f8'),('Voff','<f8'),\
                                ('b_to_a','<f8'),('c_to_a','<f8'),('A[x]','<f8'),('A[y]','<f8'),('A[z]','<f8'),\
                                ('spin_bullock','<f8'),('T/|U|','<f8'),\
                                ('npart','<i8'),('num_cp','<i8'),('numstart','<i8'),\
                                ('desc','<i8'),('flags','<i8'),('n_core','<i8'),\
                                ('min_pos_err','<f8'),('min_vel_err','<f8'),('min_bulkvel_err','<f8'),\
                                ('hostID','<i8'),('offset','<i8'),('particle_offset','<i8')])
            datatypesstr = "qffffffffffffffffffffffffffffffffffffffffqqqqqqxxxxfff"
            numbytes = struct.calcsize(datatypesstr) #232
        if version==3: #RC2
            headerfmt = "qqqffffffffffqqffq"+"x"*(256-96)
            varlist = np.dtype([('id','<i8'),\
                                ('posX','<f8'),('posY','<f8'),('posZ','<f8'),\
                                ('pecVX','<f8'),('pecVY','<f8'),('pecVZ','<f8'),\
                                ('corevelx','<f8'),('corevely','<f8'),('corevelz','<f8'),\
                                ('bulkvelx','<f8'),('bulkvely','<f8'),('bulkvelz','<f8'),\
                                ('mvir','<f8'),('rvir','<f8'),('child_r','<f8'),('vmax_r','<f8'),\
                                ('mgrav','<f8'),('vmax','<f8'),('rvmax','<f8'),('rs','<f8'),('rs_klypin','<f8'),\
                                ('vrms','<f8'),('Jx','<f8'),('Jy','<f8'),('Jz','<f8'),\
                                ('Epot','<f8'),('spin','<f8'),('altm1','<f8'),('altm2','<f8'),('altm3','<f8'),('altm4','<f8'),\
                                ('Xoff','<f8'),('Voff','<f8'),\
                                ('b_to_a','<f8'),('c_to_a','<f8'),('A[x]','<f8'),('A[y]','<f8'),('A[z]','<f8'),\
                                ('b_to_a2','<f8'),('c_to_a2','<f8'),('A2[x]','<f8'),('A2[y]','<f8'),('A2[z]','<f8'),\
                                ('spin_bullock','<f8'),('T/|U|','<f8'),\
                                ('npart','<i8'),('num_cp','<i8'),('numstart','<i8'),\
                                ('desc','<i8'),('flags','<i8'),('n_core','<i8'),\
                                ('min_pos_err','<f8'),('min_vel_err','<f8'),('min_bulkvel_err','<f8'),\
                                ('hostID','<i8'),('offset','<i8'),('particle_offset','<i8')])
            datatypesstr = "qfffffffffffffffffffffffffffffffffffffffffffffqqqqqqxxxxfff"
            numbytes = struct.calcsize(datatypesstr) #256
        if version==4: #RC2 with numbound
            headerfmt = "qqqffffffffffqqffq"+"x"*(256-96)
            varlist = np.dtype([('id','<i8'),\
                                ('posX','<f8'),('posY','<f8'),('posZ','<f8'),\
                                ('pecVX','<f8'),('pecVY','<f8'),('pecVZ','<f8'),\
                                ('corevelx','<f8'),('corevely','<f8'),('corevelz','<f8'),\
                                ('bulkvelx','<f8'),('bulkvely','<f8'),('bulkvelz','<f8'),\
                                ('mvir','<f8'),('rvir','<f8'),('child_r','<f8'),('vmax_r','<f8'),\
                                ('mgrav','<f8'),('vmax','<f8'),('rvmax','<f8'),('rs','<f8'),('rs_klypin','<f8'),\
                                ('vrms','<f8'),('Jx','<f8'),('Jy','<f8'),('Jz','<f8'),\
                                ('Epot','<f8'),('spin','<f8'),('altm1','<f8'),('altm2','<f8'),('altm3','<f8'),('altm4','<f8'),\
                                ('Xoff','<f8'),('Voff','<f8'),\
                                ('b_to_a','<f8'),('c_to_a','<f8'),('A[x]','<f8'),('A[y]','<f8'),('A[z]','<f8'),\
                                ('b_to_a2','<f8'),('c_to_a2','<f8'),('A2[x]','<f8'),('A2[y]','<f8'),('A2[z]','<f8'),\
                                ('spin_bullock','<f8'),('T/|U|','<f8'),\
                                ('npart','<i8'),('num_cp','<i8'),('numstart','<i8'),\
                                ('desc','<i8'),('flags','<i8'),('n_core','<i8'),\
                                ('min_pos_err','<f8'),('min_vel_err','<f8'),('min_bulkvel_err','<f8'),\
                                ('num_bound','<i8'),\
                                ('hostID','<i8'),('offset','<i8'),('particle_offset','<i8')])
            datatypesstr = "qfffffffffffffffffffffffffffffffffffffffffffffqqqqqqxxxxfffq"
            numbytes = struct.calcsize(datatypesstr) #260
        if version==5: #modification to include total num bound particles and tidal radius
            # corresponds to rockstar version here: /spacebase/data/gdooley/RockstarSorted/rockstarTidal 
            # with TIDAL defined. halo.h and properties.c are modified.
            headerfmt = "qqqffffffffffqqffq"+"x"*(256-96)
            varlist = np.dtype([('id','<i8'),\
                                ('posX','<f8'),('posY','<f8'),('posZ','<f8'),\
                                ('pecVX','<f8'),('pecVY','<f8'),('pecVZ','<f8'),\
                                ('corevelx','<f8'),('corevely','<f8'),('corevelz','<f8'),\
                                ('bulkvelx','<f8'),('bulkvely','<f8'),('bulkvelz','<f8'),\
                                ('mvir','<f8'),('rvir','<f8'),('child_r','<f8'),('vmax_r','<f8'),\
                                ('mgrav','<f8'),('vmax','<f8'),('rvmax','<f8'),('rs','<f8'),('rs_klypin','<f8'),\
                                ('vrms','<f8'),('Jx','<f8'),('Jy','<f8'),('Jz','<f8'),\
                                ('Epot','<f8'),('spin','<f8'),('altm1','<f8'),('altm2','<f8'),('altm3','<f8'),('altm4','<f8'),\
                                ('Xoff','<f8'),('Voff','<f8'),\
                                ('b_to_a','<f8'),('c_to_a','<f8'),('A[x]','<f8'),('A[y]','<f8'),('A[z]','<f8'),\
                                ('b_to_a2','<f8'),('c_to_a2','<f8'),('A2[x]','<f8'),('A2[y]','<f8'),('A2[z]','<f8'),\
                                ('spin_bullock','<f8'),('T/|U|','<f8'),\
                                ('npart','<i8'),('num_cp','<i8'),('numstart','<i8'),\
                                ('desc','<i8'),('flags','<i8'),('n_core','<i8'),\
                                ('min_pos_err','<f8'),('min_vel_err','<f8'),('min_bulkvel_err','<f8'),\
                                ('num_bound','<i8'),('tidal_r','<f8'),\
                                ('hostID','<i8'),('offset','<i8'),('particle_offset','<i8')])
            datatypesstr = "qfffffffffffffffffffffffffffffffffffffffffffffqqqqqqxxxxfffqfxxxx"
            numbytes = struct.calcsize(datatypesstr) #264
        if version==6: #RC3, HDF5-compatible rockstar with pseudoevolution-corrected masses
            headerfmt = "qqqffffffffffqqffq"+"x"*(256-96)
            varlist = np.dtype([('id','<i8'),\
                                ('posX','<f8'),('posY','<f8'),('posZ','<f8'),\
                                ('pecVX','<f8'),('pecVY','<f8'),('pecVZ','<f8'),\
                                ('corevelx','<f8'),('corevely','<f8'),('corevelz','<f8'),\
                                ('bulkvelx','<f8'),('bulkvely','<f8'),('bulkvelz','<f8'),\
                                ('mvir','<f8'),('rvir','<f8'),('child_r','<f8'),('vmax_r','<f8'),\
                                ('mgrav','<f8'),('vmax','<f8'),('rvmax','<f8'),('rs','<f8'),('rs_klypin','<f8'),\
                                ('vrms','<f8'),('Jx','<f8'),('Jy','<f8'),('Jz','<f8'),\
                                ('Epot','<f8'),('spin','<f8'),('altm1','<f8'),('altm2','<f8'),('altm3','<f8'),('altm4','<f8'),\
                                ('Xoff','<f8'),('Voff','<f8'),\
                                ('b_to_a','<f8'),('c_to_a','<f8'),('A[x]','<f8'),('A[y]','<f8'),('A[z]','<f8'),\
                                ('b_to_a2','<f8'),('c_to_a2','<f8'),('A2[x]','<f8'),('A2[y]','<f8'),('A2[z]','<f8'),\
                                ('spin_bullock','<f8'),('T/|U|','<f8'),\
                                ('m_pe_b','<f8'),('m_pe_d','<f8'),\
                                ('npart','<i8'),('num_cp','<i8'),('numstart','<i8'),\
                                ('desc','<i8'),('flags','<i8'),('n_core','<i8'),\
                                ('min_pos_err','<f8'),('min_vel_err','<f8'),('min_bulkvel_err','<f8'),\
                                ('hostID','<i8'),('offset','<i8'),('particle_offset','<i8')])
            datatypesstr = "qfffffffffffffffffffffffffffffffffffffffffffffffqqqqqqxxxxfff"
            numbytes = struct.calcsize(datatypesstr) #264
        if version==7: #RC3, HDF5-compatible rockstar with pseudoevolution-corrected masses, total_num_p added, and full particle binary output support. 8/19/2014
            headerfmt = "qqqffffffffffqqffq"+"x"*(256-96)
            varlist = np.dtype([('id','<i8'),\
                                ('posX','<f8'),('posY','<f8'),('posZ','<f8'),\
                                ('pecVX','<f8'),('pecVY','<f8'),('pecVZ','<f8'),\
                                ('corevelx','<f8'),('corevely','<f8'),('corevelz','<f8'),\
                                ('bulkvelx','<f8'),('bulkvely','<f8'),('bulkvelz','<f8'),\
                                ('mvir','<f8'),('rvir','<f8'),('child_r','<f8'),('vmax_r','<f8'),\
                                ('mgrav','<f8'),('vmax','<f8'),('rvmax','<f8'),('rs','<f8'),('rs_klypin','<f8'),\
                                ('vrms','<f8'),('Jx','<f8'),('Jy','<f8'),('Jz','<f8'),\
                                ('Epot','<f8'),('spin','<f8'),('altm1','<f8'),('altm2','<f8'),('altm3','<f8'),('altm4','<f8'),\
                                ('Xoff','<f8'),('Voff','<f8'),\
                                ('b_to_a','<f8'),('c_to_a','<f8'),('A[x]','<f8'),('A[y]','<f8'),('A[z]','<f8'),\
                                ('b_to_a2','<f8'),('c_to_a2','<f8'),('A2[x]','<f8'),('A2[y]','<f8'),('A2[z]','<f8'),\
                                ('spin_bullock','<f8'),('T/|U|','<f8'),\
                                ('m_pe_b','<f8'),('m_pe_d','<f8'),\
                                ('npart','<i8'),('num_cp','<i8'),('numstart','<i8'),\
                                ('desc','<i8'),('flags','<i8'),('n_core','<i8'),\
                                ('min_pos_err','<f8'),('min_vel_err','<f8'),('min_bulkvel_err','<f8'),\
                                ('total_npart','<i8'),\
                                ('hostID','<i8'),('offset','<i8'),('particle_offset','<i8')])
            datatypesstr = "qfffffffffffffffffffffffffffffffffffffffffffffffqqqqqqxxxxfffq"
            numbytes = struct.calcsize(datatypesstr) #264
        if version==8: #RC3+, full particle binary and half mass radius. 10/15/2014
            headerfmt = "qqqffffffffffqqffq"+"x"*(256-96)
            varlist = np.dtype([('id','<i8'),\
                                ('posX','<f8'),('posY','<f8'),('posZ','<f8'),\
                                ('pecVX','<f8'),('pecVY','<f8'),('pecVZ','<f8'),\
                                ('corevelx','<f8'),('corevely','<f8'),('corevelz','<f8'),\
                                ('bulkvelx','<f8'),('bulkvely','<f8'),('bulkvelz','<f8'),\
                                ('mvir','<f8'),('rvir','<f8'),('child_r','<f8'),('vmax_r','<f8'),\
                                ('mgrav','<f8'),('vmax','<f8'),('rvmax','<f8'),('rs','<f8'),('rs_klypin','<f8'),\
                                ('vrms','<f8'),('Jx','<f8'),('Jy','<f8'),('Jz','<f8'),\
                                ('Epot','<f8'),('spin','<f8'),('altm1','<f8'),('altm2','<f8'),('altm3','<f8'),('altm4','<f8'),\
                                ('Xoff','<f8'),('Voff','<f8'),\
                                ('b_to_a','<f8'),('c_to_a','<f8'),('A[x]','<f8'),('A[y]','<f8'),('A[z]','<f8'),\
                                ('b_to_a2','<f8'),('c_to_a2','<f8'),('A2[x]','<f8'),('A2[y]','<f8'),('A2[z]','<f8'),\
                                ('spin_bullock','<f8'),('T/|U|','<f8'),\
                                ('m_pe_b','<f8'),('m_pe_d','<f8'),('halfmassrad','<f8'),\
                                ('npart','<i8'),('num_cp','<i8'),('numstart','<i8'),\
                                ('desc','<i8'),('flags','<i8'),('n_core','<i8'),\
                                ('min_pos_err','<f8'),('min_vel_err','<f8'),('min_bulkvel_err','<f8'),\
                                ('total_npart','<i8'),\
                                ('hostID','<i8'),('offset','<i8'),('particle_offset','<i8')])
            datatypesstr = "qffffffffffffffffffffffffffffffffffffffffffffffffqqqqqqfffq"
            numbytes = struct.calcsize(datatypesstr)
        if version==9 or version==10: # Alex's iterunbind. Added Feb 4, 2015
            headerfmt = "qqqffffffffffqqffq"+"x"*(256-96)
            varlist = np.dtype([('id','<i8'),\
                        ('posX','<f8'),('posY','<f8'),('posZ','<f8'),\
                        ('pecVX','<f8'),('pecVY','<f8'),('pecVZ','<f8'),\
                        ('corevelx','<f8'),('corevely','<f8'),('corevelz','<f8'),\
                        ('bulkvelx','<f8'),('bulkvely','<f8'),('bulkvelz','<f8'),\
                        ('mvir','<f8'),('rvir','<f8'),('child_r','<f8'),('vmax_r','<f8'),\
                        ('mgrav','<f8'),('vmax','<f8'),('rvmax','<f8'),('rs','<f8'),('rs_klypin','<f8'),\
                        ('vrms','<f8'),('Jx','<f8'),('Jy','<f8'),('Jz','<f8'),\
                        ('Epot','<f8'),('spin','<f8'),('altm1','<f8'),('altm2','<f8'),('altm3','<f8'),('altm4','<f8'),\
                        ('Xoff','<f8'),('Voff','<f8'),\
                        ('b_to_a','<f8'),('c_to_a','<f8'),('A[x]','<f8'),('A[y]','<f8'),('A[z]','<f8'),\
                        ('b_to_a2','<f8'),('c_to_a2','<f8'),('A2[x]','<f8'),('A2[y]','<f8'),('A2[z]','<f8'),\
                        ('spin_bullock','<f8'),('T/|U|','<f8'),\
                        ('m_pe_b','<f8'),('m_pe_d','<f8'),('halfmassrad','<f8'),\
                        ('npart','<i8'),('num_cp','<i8'),('numstart','<i8'),\
                        ('desc','<i8'),('flags','<i8'),('n_core','<i8'),\
                        ('min_pos_err','<f8'),('min_vel_err','<f8'),('min_bulkvel_err','<f8'),\
                        ('num_bound','<i8'),('num_iter','<i8'),\
                        ('hostID','<i8'),('offset','<i8'),('particle_offset','<i8')])
            datatypesstr = "qffffffffffffffffffffffffffffffffffffffffffffffffqqqqqqfffqq"
            #datatypesstr = "qfffffffffffffffffffffffffffffffffffffffffffffffqqqqqqxxxxfffqq"
            numbytes = struct.calcsize(datatypesstr) #264

        self.datatypesstr = datatypesstr

        file_num = 0
        file_name = getfilename(file_num)
        if (not os.path.exists(file_name)):
            raise IOError("ERROR: file not found "+file_name)
            
        ## Count total number of particles/halos in all data blocks
        self.num_halos = 0
        self.total_particles = 0  #AllParticles
        while os.path.exists(file_name):
            f = open(file_name)
            h = f.read(numheaderbytes)
            (magic,self.snap_num,chunk,self.scale,self.Om,self.Ol,self.h0,\
             bounds1,bounds2,bounds3,bounds4,bounds5,bounds6,\
             num_halos,num_particles,\
             self.boxsize,self.particle_mass,self.particle_type) = struct.unpack(headerfmt,h)
            self.num_halos += num_halos
            self.total_particles += num_particles #AllParticles
            f.close()
            file_num += 1
            file_name = getfilename(file_num)
        ## Initialize empty data structure
        data = np.zeros(self.num_halos,dtype=varlist)
        files = np.array(['']*self.num_halos, dtype='|S'+str(len(file_name)*2))
        if AllParticles:
            self.particles = np.array([])
            # self.particles=np.array([-1]*self.total_particles)

        ## Now, read in the actual data
        file_num = 0 # reset file name
        file_name = getfilename(file_num)
        i = 0
        particleID_start2 = 0 
        while os.path.exists(file_name):
            f = open(file_name)
            h = f.read(numheaderbytes)
            num_halos,num_particles = struct.unpack(("x"*64)+"qq"+("x"*16)+"x"*(256-96),h)            
            # note this is current block's num_halos, not the total self.num_halos
            particleID_start = struct.calcsize(headerfmt)+num_halos*struct.calcsize(datatypesstr)

            for j in xrange(num_halos):
                line = f.read(numbytes)
                data[i] = struct.unpack(datatypesstr,line)+(0,0,0)
                data[i][-2] = particleID_start  # offset
                data[i][-1] = particleID_start2 # particle_offset
                files[i] = file_name
                particleID_start  += self.particlebytes * data[self.num_p][i]
                particleID_start2 += data[self.num_p][i]
                i += 1

            if AllParticles:
                line = f.read() # read the rest of the file
                ## DEBUG: this ratio should be 1
                if num_particles != 0:
                    #assert(len(line)/float(self.particlebytes))/num_particles == 1
                    nppf=int(len(line)/float(self.particlebytes))
                    self.particles = np.concatenate((self.particles, np.array(struct.unpack("q"*nppf,line))))
                    #self.particles[part_fpos:part_fpos+num_particles]=np.array(struct.unpack("q"*num_particles,line))
            f.close()
            file_num += 1
            file_name = getfilename(file_num)

        if sort_by != None:
            sortedIndices = data[sort_by].argsort()[::-1]
            data = data[sortedIndices]
            files= files[sortedIndices]

        if len(files)==0:
            raise RuntimeError("No halos in snap %i" % (snap_num))

        self.files = pandas.DataFrame(files, index=data['id'].astype(int),columns=['file'])
        self.data = pandas.DataFrame(data,index=data['id'])

        if AllParticles:
            self.particles = self.particles.astype(int)

        if not noparents:
            parents = rp.readParents(dir+'/'+base+str(snap_num).zfill(digits),'parents.list',self.num_halos)
            self.data['hostID'].ix[parents[:,0]] = parents[:,1]

        assert (unboundfrac == None) or (minboundpart == None)
        self.unboundfrac = unboundfrac
        if unboundfrac != None:
            assert unboundfrac >= 0.0 and unboundfrac <= 1.0
            iibound = self.data['mgrav']/self.data['mvir'] > unboundfrac
            iiunbound = self.data['mgrav']/self.data['mvir'] <= unboundfrac
            self.unbounddata = self.data.ix[iiunbound]
            self.data = self.data.ix[iibound]
            self.num_halos = len(self.data)
        self.minboundpart = minboundpart
        if minboundpart != None:
            assert minboundpart >= 0
            boundindex = load_rsboundindex(self.dir+'/..',self.snap_num)
            boundrows = boundindex['numbound'] >= minboundpart
            iibound   = boundindex['hid'][boundrows]
            iiunbound = boundindex['hid'][~boundrows]
            self.boundindex = boundindex
            self.unbounddata = self.data.ix[iiunbound]
            self.data = self.data.ix[iibound]
            self.num_halos = len(self.data)

        self.ix = self.data.ix
        self.index = self.data.index

    def get_particles_from_halo(self, haloID):
        """
        @param haloID: id number of halo. Not its row position in matrix
        @return: a list of particle IDs in the Halo

        3/25 change: if AllParticles is on, haloID can be a vector.
        """
        if self.AllParticles:
            if type(haloID) == list or type(haloID) == np.ndarray:
                return np.array([ self.particles[self.data['particle_offset'].ix[ID]: self.data['particle_offset'].ix[ID]+self.data[self.num_p].ix[ID]] for ID in haloID])
            else:
                start = self.data['particle_offset'].ix[haloID]
                end = start+self.data[self.num_p].ix[haloID]
                return self.particles[start:end]
        else:
            f = open(self.files['file'].ix[haloID])
            #np.fromfile(f,'c',count=int(self.data['offset'].ix[haloID])) # might be marginally slower than seek
            f.seek(int(self.data['offset'].ix[haloID]),0)
            particleIDs = np.fromfile(f,np.int64,count=int(self.data[self.num_p].ix[haloID]))
            f.close()
            return particleIDs

    def get_subhalos_from_halo(self,haloID):
        """
        # Retrieve subhalos only one level deep.
        # Does not get sub-sub halos, etc.
        """
        return self.data[self.data['hostID']==haloID]

    def get_subhalos_from_halos(self,haloIDs):
        """
        returns an array of pandas data frames of subhalos. one data frame
        for each host halo. returns only first level of subhalos.
        # for multiple halos, returns the subhalos of each halo as an array of arrays.
        """
        if type(haloIDs) == list or type(haloIDs) == np.ndarray:
            return np.array([ self.data[self.data['hostID']==ID] for ID in haloIDs])
        else:
            return self.data[self.data['hostID']==haloIDs] 

    def get_subhalos_from_halos_flat(self,haloIDs):
        """
        returns a flattened pandas data frame of all subhalos within
        the hosts given by haloIDs. Returns only first level of subhalos.
        """
        subs = self.get_subhalo_ids_from_halos(haloIDs)
        subIDs = [item for sublist in subs for item in sublist]
        return self.data.ix[subIDs]
    
    def get_hosts(self):
        return self.data[self.data['hostID']==-1]

    def get_subs(self):
        return self.data[self.data['hostID']!=-1]

    def get_subhalo_ids_from_halos(self,haloIDs):
        if type(haloIDs) == list or type(haloIDs) == np.ndarray:
            return np.array([ np.array(self.data[self.data['hostID']==ID]['id']) for ID in haloIDs])
        else:
            return np.array([self.data[self.data['hostID']==haloIDs]['id']])

    def get_all_subs_recurse(self,haloID):
        """
        # Retrieve all subhalos: sub and sub-sub, etc. 
        # just need mask of all subhalos, then return data frame subset
        """
        subs = self.get_subhalo_ids_from_halos(haloID)
        subs = [item for sublist in subs for item in sublist]
        if subs == []:
            return [] 
        else:
            return np.append(subs,self.get_all_subs_recurse(subs))
                                       
    def get_all_subhalos_from_halo(self,haloID):
        """
        # Retrieve all subhalos: sub and sub-sub, etc.
        # return pandas data fram of subhalos
        """
        return self.data.ix[self.get_all_subs_recurse(haloID)]

        
    def get_subhalos_within_halo(self, haloID, radius=None):
        """
        # return all halos within radis of halo specified by haloID
        # that are only 1 level deep subhaloes
        # radius specified in kpc
        """
        if radius==None:
            radius = float(self.ix[haloID]['rvir'])
        dists = distance(np.array(self[['posX','posY','posZ']]), np.array(self.ix[haloID][['posX','posY','posZ']]))*1000
        halos = self[(dists<radius)*(dists>0)] # exclude host
        halos = halos[np.logical_or(halos['hostID']==haloID,halos['hostID']==-1)] # only take 1 level deep halos
        return halos

    def get_all_subhalos_within_halo(self, haloID, radius=None):
        """
        # return all halos within radis of halo specified by haloID
        # radius specified in kpc
        """
        if radius==None:
            radius = float(self.ix[haloID]['rvir'])
        dists = distance(np.array(self[['posX','posY','posZ']]), np.array(self.ix[haloID][['posX','posY','posZ']]))*1000
        halos = self[(dists<radius)*(dists>0)] # exclude host
        return halos
                

    def get_all_sub_particles_from_halo(self,haloID):
        """
        returns int array of particle IDs belonging to all substructure
        within host of haloID
        # updated 3/26 2013 to include support for array/list input of haloID. Also streamlined the code.
        """
        if type(haloID) == list or type(haloID)==np.ndarray:
            if self.version>=7:
                subids = [self.get_subhalos_from_halo(id)['id'] for id in haloID]
            else:
                subids = [self.get_all_subhalos_from_halo(id)['id'] for id in haloID]
            idlist = [[item for s in sid for item in self.get_particles_from_halo(s)] for sid in subids]
            return idlist
        else:
            if self.version>=7:
                subids = self.get_subhalos_from_halo(haloID)['id']
            else:
                subids = self.get_all_subhalos_from_halo(haloID)['id']
            return [item for s in subids for item in self.get_particles_from_halo(s)]
            # old method
            # idlist = np.array([])
            #for sid in subids:
            #    idlist = np.append(idlist, self.get_particles_from_halo(sid))
            #return idlist.astype(int)

    def get_all_particles_from_halo(self,haloID):
        """
        returns int array of all particles belonging to haloID
        """
        if self.version>=7:
            return self.get_particles_from_halo(haloID)
        return np.append(self.get_particles_from_halo(haloID), self.get_all_sub_particles_from_halo(haloID)).astype(int)


    def get_all_num_particles_from_halo(self,haloID):
        if self.version==10:
            return self.data.ix[haloID]['num_bound']
        elif self.version==7 or self.version==8:
            return self.data.ix[haloID]['total_npart']
        thisnum = self.data.ix[haloID]['npart']
        subdat = self.get_all_subhalos_from_halo(haloID)
        return thisnum + np.sum(subdat['npart'])

    def get_bound_particles_from_halo(self,haloID):
        assert self.minboundpart != None        
        ixid = self.boundindex['hid']
        row = np.where(ixid==haloID)[0][0]
        loc = self.boundindex[row]['loc']
        numbound = self.boundindex[row]['numbound']
        fmt = "q"*numbound
        with open(self.boundpartspath,'rb') as f:
            f.seek(loc)
            line = f.read(struct.calcsize(fmt))
            boundids = struct.unpack(fmt,line)
        return boundids
        
    def get_block_from_halo(self, snapshot_dir, haloID, blockname, allparticles=True):
        if allparticles:
            pids = self.get_all_particles_from_halo(haloID)
        else:
            pids = self.get_particles_from_halo(haloID)
        pids = np.sort(pids)
        path = snapshot_dir+'/snapdir_'+str(self.snap_num).zfill(3)+'/snap_'+str(self.snap_num).zfill(3)
        return rsg.read_block(path, blockname,parttype=1,ids=pids)

    # compute hubble value for this catalogue
    # return value in km/s/Mpc
    def H(self):
        to_inv_sec = 3.241*10**-20
        Ok = 1-self.Om-self.Ol
        a = self.scale
        return 100*self.h0*(self.Om*(1/a)**3 + Ok*(1/a)**2 + self.Ol)**.5

    # get most bound particles according to grav potential only
    def get_most_gravbound_particles_from_halo(self,snapshot_dir, haloID):
        pids = self.get_all_particles_from_halo(haloID)
        pids = np.sort(pids)
        path = snapshot_dir+'/snapdir_'+str(self.snap_num).zfill(3)+'/snap_'+str(self.snap_num).zfill(3)
        pot = rsg.read_block(path, "POT ", parttype=1, ids=pids)/self.scale
        boundsort = np.argsort(pot)
        return pids[boundsort]

    # Get most bound particles in a halo
    # Use gadget Potential block if it exists, otherwise compute estimate of it.
    def get_most_bound_particles_from_halo(self, snapshot_dir, haloID):
        pids = self.get_all_particles_from_halo(haloID)
        pids = np.sort(pids)
        path = snapshot_dir+'/snapdir_'+str(self.snap_num).zfill(3)+'/snap_'+str(self.snap_num).zfill(3)
    
        pos = rsg.read_block(path, "POS ", parttype=1, ids=pids)
        vel = rsg.read_block(path, "VEL ", parttype=1, ids=pids)*np.sqrt(self.scale)
        halopos = np.array(self.ix[haloID][['posX','posY','posZ']])
        halovel = np.array(self.ix[haloID][['pecVX','pecVY','pecVZ']])
        
        peculiarVel = vel-halovel
        Hflow = self.H()*(pos-halopos)*self.scale/self.h0
        physicalVel = peculiarVel+Hflow
        T = .5*sum((physicalVel**2).T)    

        try:
            U = rsg.read_block(path, "POT ", parttype=1, ids=pids)/self.scale
        except:
            print 'computing potential instead'
            dr = distance(pos,halopos,boxsize=self.boxsize)*self.scale/self.h0#in Mpc physical
            mask = dr==0
            dr=dr[~mask]
            U = self.PotentialE(dr)

        Etot = T + U
        boundsort = np.argsort(Etot)
        return pids[boundsort]

    def get_bound_subhalos_from_halo(self, hpath,haloID):
        subids = np.array(self.get_all_subhalos_from_halo(haloID)['id'])
        #print subids
        pos = np.array(self.ix[subids][['posX','posY','posZ']])
        vel = np.array(self.ix[subids][['corevelx','corevely','corevelz']])
        halopos = np.array(self.ix[haloID][['posX','posY','posZ']])
        halovel = np.array(self.ix[haloID][['corevelx','corevely','corevelz']])
        
        peculiarVel = vel-halovel
        Hflow = self.H()*(pos-halopos)*self.scale/self.h0
        physicalVel = peculiarVel+Hflow
        T = .5*sum((physicalVel**2).T)    

        drhalos = distance(pos,halopos,boxsize=self.boxsize)*self.scale/self.h0#in Mpc physical

        pids = self.get_all_particles_from_halo(haloID)
        path = hpath+'/outputs/snapdir_'+str(self.snap_num).zfill(3)+'/snap_'+str(self.snap_num).zfill(3)
    
        ppos = rsg.read_block(path, "POS ", parttype=1, ids=np.sort(pids))
        drp = distance(ppos,halopos,boxsize=self.boxsize)*self.scale/self.h0#in Mpc physical
        mask = drp==0
        drp=drp[~mask]
        U = self.PotentialE_halos(drp,drhalos)

        Etot = T + U
        boundsort = np.argsort(Etot)
        return T[boundsort],U[boundsort],Etot[boundsort],subids[boundsort]

    def PotentialE_halos(self, dr,drhalos):
        from scipy import interpolate
        from scipy.integrate import quad
        G = 1.326*10**11 # in km^3/s^2/Msun
        mpc_to_km = 3.086*10**19
        
        rarr = 10**np.linspace(np.log10(min(dr))-.01, np.log10(max(dr))+.01,70) # in Mpc
        h_r, x_r = np.histogram(dr, bins=np.concatenate(([0],rarr)))
        m_lt_r = np.cumsum(h_r)*self.particle_mass/self.h0
        tck = interpolate.splrep(rarr,m_lt_r) # gives mass in Msun
        def Ufunc(x):
            return interpolate.splev(x,tck)/(x**2)
    
        # do it even faster by using an interpolative function
        # for computing potential energy
        # pick 60 - 100 data points
        # compute potential for all, then use an interpolation scheme
        U = np.zeros(len(rarr))
        for i in range(len(rarr)):
            r = rarr[i]
            if r > max(dr)+.05:
                print 'warning - particle outside of halo. likely inaccurate PE'
                U[i] = -G*m_lt_r[-1]/(r*mpc_to_km)
            else:
                tmp = -G*m_lt_r[-1]/(max(dr)*mpc_to_km)
                U[i] = tmp+G*quad(Ufunc,max(dr),r,full_output=1)[0]/mpc_to_km
        tck2 = interpolate.splrep(rarr,U)
        return interpolate.splev(drhalos,tck2)

    def PotentialE(self, dr):
        from scipy import interpolate
        from scipy.integrate import quad
        G = 1.326*10**11 # in km^3/s^2/Msun
        mpc_to_km = 3.086*10**19
        
        rarr = 10**np.linspace(np.log10(min(dr))-.01, np.log10(max(dr))+.01,70) # in Mpc
        h_r, x_r = np.histogram(dr, bins=np.concatenate(([0],rarr)))
        m_lt_r = np.cumsum(h_r)*self.particle_mass/self.h0
        tck = interpolate.splrep(rarr,m_lt_r) # gives mass in Msun
        def Ufunc(x):
            return interpolate.splev(x,tck)/(x**2)
    
        # do it even faster by using an interpolative function
        # for computing potential energy
        # pick 60 - 100 data points
        # compute potential for all, then use an interpolation scheme
        U = np.zeros(len(rarr))
        for i in range(len(rarr)):
            r = rarr[i]
            if r > max(dr)+.05:
                print 'warning - particle outside of halo. likely inaccurate PE'
                U[i] = -G*m_lt_r[-1]/(r*mpc_to_km)
            else:
                tmp = -G*m_lt_r[-1]/(max(dr)*mpc_to_km)
                U[i] = tmp+G*quad(Ufunc,max(dr),r,full_output=1)[0]/mpc_to_km
        tck2 = interpolate.splrep(rarr,U)
        return interpolate.splev(dr,tck2)

    def getversion(self):
        if self.version == 2:
            return "Version 2: Rockstar 0.99.9 RC1"
        if self.version == 3:
            return "Version 3: Rockstar 0.99.9 RC2"
        if self.version == 4:
            return "Version 4: Rockstar 0.99.9 RC2 with numbound"
        if self.version == 5:
            return "Version 5: Rockstar 0.99.9 RC2 with numbound and tidal (Greg)"
        if self.version == 6:
            return "Version 6: Rockstar 0.99.9 RC3"
        if self.version == 7:
            return "Version 7: Rockstar 0.99.9 RC3 with full particles on"
        if self.version == 8:
            return "Version 8: Rockstar 0.99.9 RC3+/4 with full particles on"
        if self.version == 9:
            return "Version 9: Rockstar 0.99.9 RC3+/4 with only bound particles (NOT USED ANYMORE)"
        if self.version == 10:
            return "Version 10: Rockstar 0.99.9 RC3+/4 with only bound particles"
        return "ERROR: Not a valid version number!"


    def to_ascii(self,filename):
        assert self.version==10
        with open(filename,'w') as f:
            # print first line to match rockstar
            f.write("#id num_p mvir mbound_vir rvir vmax rvmax vrms x y z vx vy vz Jx Jy Jz E Spin PosUncertainty VelUncertainty bulk_vx bulk_vy bulk_vz BulkVelUnc n_core m200b m200c m500c m2500c Xoff Voff spin_bullock b_to_a c_to_a A[x] A[y] A[z] b_to_a(500c) c_to_a(500c) A[x](500c) A[y](500c) A[z](500c) Rs Rs_Klypin T/|U| M_pe_Behroozi M_pe_Diemer Halfmass_Radius idx i_so i_ph num_cp mmetric\n")
            # First line for modified version
            #f.write("#id num_p mvir mbound_vir rvir vmax rvmax vrms x y z vx vy vz Jx Jy Jz E Spin PosUncertainty VelUncertainty bulk_vx bulk_vy bulk_vz BulkVelUnc n_core m200b m200c m500c m2500c Xoff Voff spin_bullock b_to_a c_to_a A[x] A[y] A[z] b_to_a(500c) c_to_a(500c) A[x](500c) A[y](500c) A[z](500c) Rs Rs_Klypin T/|U| M_pe_Behroozi M_pe_Diemer Halfmass_Radius num_cp num_bound num_iter \n")

            # print header info
            f.write("#a = {0}\n".format(self.scale))
            f.write("#FOF linking length: 0.28\n")
            f.write("#Om = {0}; Ol = {1}; h = {2}\n".format(self.Om,self.Ol,self.h0))
            f.write("#Unbound Threshold: NA; FOF Refinement Threshold: 0.7\n")
            f.write("#Particle mass: {0:.5e} Msun/h\n".format(self.particle_mass))
            f.write("#Box size: {0} Mpc/h\n".format(self.boxsize))
            #f.write("#Total particles processed: NA\n")
            #f.write("#Force resolution assumed: NA Mpc/h\n")
            f.write("#Units: Masses in Msun / h\n")
            f.write("#Units: Positions in Mpc / h (comoving)\n")
            f.write("#Units: Velocities in km / s (physical, peculiar)\n")
            f.write("#Units: Halo Distances, Lengths, and Radii in kpc / h (comoving)\n")
            f.write("#Units: Angular Momenta in (Msun/h) * (Mpc/h) * km/s (physical)\n")
            f.write("#Units: Spins are dimensionless\n")
            f.write("#Units: Total energy in (Msun/h)*(km/s)^2 (physical)\n")

            # loop through and print halos
            # These are to match rockstar directly, including the unsaved debug quantities. Note I haven't taken the sqrt of the uncertainties.
            cols = ['id','npart','mvir','mgrav','rvir','vmax','rvmax','vrms','posX','posY','posZ','pecVX','pecVY','pecVZ','Jx','Jy','Jz','Epot','spin','min_pos_err','min_vel_err','bulkvelx','bulkvely','bulkvelz','min_bulkvel_err','n_core','altm1','altm2','altm3','altm4','Xoff','Voff','spin_bullock','b_to_a','c_to_a','A[x]','A[y]','A[z]','b_to_a2','c_to_a2','A2[x]','A2[y]','A2[z]','rs','rs_klypin','T/|U|','m_pe_b','m_pe_d','halfmassrad','num_cp']
            fmt = "%i %i %.3e %.3e %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %i %e %e %e %e %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f 0 0 0 %i 0\n"
            # These are to match the modified version
            #cols = ['id','npart','mvir','mgrav','rvir','vmax','rvmax','vrms','posX','posY','posZ','pecVX','pecVY','pecVZ','Jx','Jy','Jz','Epot','spin','min_pos_err','min_vel_err','bulkvelx','bulkvely','bulkvelz','min_bulkvel_err','n_core','altm1','altm2','altm3','altm4','Xoff','Voff','spin_bullock','b_to_a','c_to_a','A[x]','A[y]','A[z]','b_to_a2','c_to_a2','A2[x]','A2[y]','A2[z]','rs','rs_klypin','T/|U|','m_pe_b','m_pe_d','halfmassrad','num_cp','num_bound','num_iter']
            #fmt = "%i %i %.3e %.3e %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %i %e %e %e %e %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %i %i %i\n"

            for i in range(self.num_halos):
                halo = self.data.iloc[i]
                data = tuple(np.array(halo[cols]))
                f.write(fmt % data)
            #        id+id_offset,
            #        th->num_p, th->m, th->mgrav, th->r, th->vmax, th->rvmax, th->vrms,
            #        th->pos[0], th->pos[1], th->pos[2], th->pos[3], th->pos[4],
            #        th->pos[5], th->J[0], th->J[1], th->J[2], th->energy, th->spin,
            #        sqrt(th->min_pos_err), sqrt(th->min_vel_err), th->bulkvel[0],
            #        th->bulkvel[1], th->bulkvel[2], sqrt(th->min_bulkvel_err),
            #        th->n_core, th->alt_m[0], th->alt_m[1], th->alt_m[2], th->alt_m[3],
            #        th->Xoff, th->Voff, th->bullock_spin, th->b_to_a, th->c_to_a,
            #        th->A[0], th->A[1], th->A[2], th->b_to_a2, th->c_to_a2,
            #        th->A2[0], th->A2[1], th->A2[2], th->rs, th->klypin_rs, th->kin_to_pot,
            #        th->m_pe_b, th->m_pe_d, th->halfmass_radius,
            #        i, extra_info[i].sub_of, extra_info[i].ph, th->num_child_particles, extra_info[i].max_metric);

    def __getitem__(self,key):
        return self.data[key]
    def __setitem__(self,key, item):
        self.data[key] = item
    def __len__(self):
        return len(self.data)
    def __repr__(self):
        out = "RSDataReader "+self.getversion()+"\n"
        out +="Read from "+self.dir+"\n"
        out +="Snap number "+str(self.snap_num)+"\n"
        out +="Number of halos: "+str(self.num_halos)+"\n"
        if self.unboundfrac != None: out += "Unbound frac: %3.2f excluded %i halos\n" % (self.unboundfrac,len(self.unbounddata))
        if self.minboundpart != None: out += "Minboundpart %i: excluded %i halos\n" % (self.minboundpart,len(self.unbounddata))
        return out + "Sorted by "+self.sort_by    


# compute distance from posA to posB.
# posA can be an array. boxsize must be in same units as positions.
def distance(posA, posB,boxsize=100.):
    dist = abs(posA-posB)
    tmp = dist > boxsize/2.0
    dist[tmp] = boxsize-dist[tmp]
    if dist.shape == (3,):
        return np.sqrt(np.sum(dist**2))
    else:
        return np.sqrt(np.sum(dist**2,axis=1))

