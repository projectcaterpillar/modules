"""
Merger Tree updated version to improve speed

Includes MTCatalogueTree, which has simple visualization built in

Old Strategy:
1) First read in file line by line searching for subhalos at a=1 and building
a python dictionary matching them to their host.
2) Read in file line by line building trees. Store halo information in a halo
object. Each time a halo is read in, search backwards in the tree (breadth
first search ordering) until its descendant is found. Connect parent and
descendant halo objects. (* note - this procedure is slow and inefficient).
3) Once host halo tree is complete, skip to subhalos in the ascii file and read
in those trees. Connect subhalo trees to the host halo tree.

New Strategy:

First 3 steps are pre-processed.

1) First read in file line by line searching for subhalos at a=1 and building
a python dictionary matching them to their host. Write this data to file in binary format to be easily read in later.

2) Convert ascii file to binary file, re-ordering it into the format of: host halo tree flag + host halo tree line by line, then subhalo tree flag + subhalo tree line by line etc. until no more subhalos. Then to second most massive host halo, etc.

3) Include ascii file with the scale-factors of everything. Make it an ascii file. Open all snapshots, read the header, get the scalefactor.

4) Load scale factor file.

5) Load binary file. Read 

read in ascii file line by line building tree.

Items kept:
Scale,id,desc_id,num_prog,pid,upid,phantom,sam_mvir,mvir,rvir,rs,vrms,mmp,scale_of_last_MM,
vmax,posX,posY,posZ,pecVX,pecVY,pecVZ,Jx,Jy,Jz,spin,bfid,dfid,origid,lastprog_dfid,
m200c_all,m200b,xoff,voff,spin_bullock,b_to_a,c_to_a,A[X/Y/Z],T/|U|

Items discarded:
desc_scale,desc_pid,Tree_root_ID,snapnum,Next_coprogenitor_depthfirst_ID,M200c,M500c,M2500c,Rs_klypin
"""

import time
import struct
import csv
import sys
import numpy as np
import itertools
import os
import pydot
import subprocess

def getScaleFactors(path,minsnap=0):
    snap_num = minsnap
    file = path + '/halos_' + str(snap_num).zfill(3) + '/halos_' + str(snap_num).zfill(3) + ".0.fullbin"
    f = open(file)
    f.close()
    if (not os.path.exists(file)):
            print "ERROR: file not found", file
            sys.exit()
    scale_list = []
    while os.path.exists(file):
        f = open(file)
        magic = np.fromfile(f, np.uint64, count = 1)[0]
        snap = np.fromfile(f, np.int64, count = 1)[0]
        chunk = np.fromfile(f, np.int64, count = 1)[0]
        scale = np.fromfile(f, np.float32, count = 1)[0]
        scale_list.append(scale)
        snap_num+=1
        file = path + '/' + 'halos_' + str(snap_num) + '/' + 'halos_' + str(snap_num) + ".0.fullbin"

    return np.array(scale_list)

class getsnap:
    """
    Class that allows you to easily turn scale factor into snap number.
    Usage:
    from mergertrees.GetScaleFactors import getsnap
    getsnap = getsnap() #create object named getsnap. Note this destroys your import!
    # also works with parentheses instead of brackets if you so desire
    getsnap[1.0]
    getsnap[[1.0,0.9,0.8]]
    

    Implementation: spline the snapnums against the scale factors, then int(round(spline))
    (So note that you can give it scale factors that aren't close to a spline)
    """
    def __init__(self,path='/spacebase/data/AnnaGroup/caterpillar/parent/RockstarData',
                 minsnap=0,maxsnap=63):
        self.minsnap = minsnap
        self.maxsnap = maxsnap
        self.scale_list = getScaleFactors(path)
        self.snap_list = range(minsnap,maxsnap+1) #minsnap to maxsnap inclusive
        self.spl = interpolate.UnivariateSpline(self.scale_list,self.snap_list,s=0)
    def getsnap(self,x):
        snap=int(round(self.spl(x)))
        if snap>max(self.snap_list):
            print "WARNING: snap is "+str(snap)+", larger than largest snap!"
        if snap<min(self.snap_list):
            print "WARNING: snap is "+str(snap)+", less than smallest snap!"
        return snap
    def __getitem__(self,key):
        try:
            return [self.getsnap(x) for x in key]
        except:
            return self.getsnap(key)
    def __call__(self,arg):
        return self.__getitem__(arg)
                    
def storeSubInfo(file):
    """
    search linearly, get line number and host halo ID for all a=0 halos.
    then put information in dictionary. Each hostID has a corresponding
    list of line numbers of its hosts.

    TODO add an option to store one level deeper!
    """
    lines = []
    hostIDs = []
    f = open(file,'r')
    line = f.readline()
    while line!='':
        if line[0:5] == "#tree":
            num = int(line[6::])
            loc = f.tell()
            line = f.readline()
            upid = int(line.split()[6]) # most massive host
            if upid != -1: #if subhalo, store hostID and location
                hostIDs.append(upid)
                lines.append(loc)
        line = f.readline()
    f.close()
    # Now create python dictionary (hash table) of hosts and sub locations
    host2sub = {}
    for i in range(len(hostIDs)):
        if hostIDs[i] in host2sub:
            host2sub[hostIDs[i]].append(lines[i])
        else:
            host2sub[hostIDs[i]]=[lines[i]]
    return host2sub

def writeline(line,fout,fmt):
    s = line.split()
    data = struct.pack(fmt,
                       float(s[0]), #scale
                       int(s[1]),   #id
                       int(s[3]),   #desc_id
                       int(s[4]),   #num_prog
                       int(s[5]),   #pid
                       int(s[6]),   #upid
                       int(s[8]),   #phantom
                       float(s[9]), #sam_mvir
                       float(s[10]),#mvir
                       float(s[11]),#rvir
                       float(s[12]),#rs
                       float(s[13]),#vrms
                       int(s[14]),  #mmp
                       float(s[15]),#scale_of_last_MM
                       float(s[16]),#vmax
                       float(s[17]),#x
                       float(s[18]),#y
                       float(s[19]),#z
                       float(s[20]),#vx
                       float(s[21]),#vy
                       float(s[22]),#vz
                       float(s[23]),#jx
                       float(s[24]),#jy
                       float(s[25]),#jz
                       float(s[26]),#spin
                       int(s[27]),  #bfid [Breadth_first_ID]
                       int(s[28]),  #dfid [Depth_first_ID]
                       int(s[30]),  #origid [Orig_halo_ID]
                       int(s[33]),  #lastprog_dfid [Last_progenitor_depthfirst_ID]
                       float(s[35]),#m200c_all
                       float(s[36]),#m200b
                       float(s[40]),#xoff
                       float(s[41]),#voff
                       float(s[42]),#spin_bullock
                       float(s[43]),#b_to_a
                       float(s[44]),#c_to_a
                       float(s[45]),#A[x]
                       float(s[46]),#A[y]
                       float(s[47]),#A[z]
                       float(s[48]))#T/|U|
    fout.write(data)

def writeline_old(line,fout,fmt):
    s = line.split()
    data = struct.pack(fmt,
                       float(s[0]), #scale
                       int(s[1]),   #id
                       int(s[3]),   #desc_id
                       int(s[4]),   #num_prog
                       int(s[5]),   #pid
                       int(s[6]),   #upid
                       float(s[9]), #mvir
                       float(s[10]),#orig_mvir
                       float(s[11]),#rvir
                       float(s[12]),#rs
                       float(s[13]),#vrms
                       int(s[14]),  #mmp
                       float(s[15]),#scale_of_last_MM
                       float(s[16]),#vmax
                       float(s[17]),#x
                       float(s[18]),#y
                       float(s[19]),#z
                       float(s[20]),#vx
                       float(s[21]),#vy
                       float(s[22]),#vz
                       float(s[23]),#jx
                       float(s[24]),#jy
                       float(s[25]),#jz
                       float(s[26]),#spin
                       int(s[27]),  #Breadth_first_ID
                       int(s[28]),  #Depth_first_ID
                       int(s[30]))  #Orig_halo_ID
    fout.write(data)

def convertmt(dir,time_me=False,oldversion=False,verbose=False):
    """
    Convert tree_0_0_0.dat ascii file to tree.bin binary file for
    faster reading. Also outputs index file

    TODO add option to store one level deeper (in the index)!
    """
    filenamein = dir+"/tree_0_0_0.dat"
    filenameout = dir+"/tree.bin"
    fileindexname = dir+"/treeindex.csv"

    if time_me:
        print "Reading subhalo positions"
        start = time.time()
    host2sub = storeSubInfo(filenamein)
    if time_me:
        print time.time()-start, 'Time to get subhalo positions'

    fin = open(filenamein,'r')
    fout= open(filenameout,'wb')
    findex=open(fileindexname,'w')
    writer = csv.writer(findex)

    if oldversion:
        fmt = "fiiiiifffffiffffffffffffiii"
        mywriteline = writeline_old
    else:
        fmt = "fiiiiiifffffiffffffffffffiiiifffffffffff"
        mywriteline = writeline
    fmtsize = struct.calcsize(fmt)
    if verbose: print "Bytes per line:",fmtsize

    line = fin.readline()
    i = 0
    while line != '':
        if line[0:5] == "#tree":
            line = fin.readline()
            hostsplit = line.split()
            ## if host halo, readwrite this halo and its subhalos
            if int(hostsplit[5]) == -1:
                if verbose:
                    print "Reading in host halo"
                    start = time.time()
                #save host ID and file location to index
                writer.writerow([hostsplit[30],fout.tell()])
                #write header tag and dummy numlines
                fout.write(struct.pack("ii",0,-1))
                numlines = 0
                #write host tree
                start2 = time.time()
                while line != '' and line[0:5] != "#tree":
                    mywriteline(line,fout,fmt)
                    numlines = numlines+1
                    line = fin.readline()
                #seek back and fill in numlines
                fout.seek(-1*(numlines*fmtsize + struct.calcsize("i")),1) #from current location backwards
                fout.write(struct.pack("i",numlines))
                fout.seek(numlines*fmtsize,1) #from current location forwards
                #remember host location to come back to after writing subs
                host_loc = fin.tell()

                ## read/write in all the subhalos
                try:
                    if verbose:
                        print time.time()-start, 'Time to read host halo',i
                        print "Reading in subhalos"
                        start = time.time()
                    for subhalo_loc in host2sub[int(hostsplit[1])]: #key is host halo id
                        #write header tag and dummy numlines
                        fout.write(struct.pack("ii",1,-1))
                        numlines = 0
                        #write sub tree
                        fin.seek(subhalo_loc) #put file head at first line of subhalo
                        line = fin.readline()
                        while line != '' and line[0:5] != "#tree":
                            numlines = numlines+1
                            mywriteline(line,fout,fmt)
                            line = fin.readline()
                        #seek back and fill in num lines
                        fout.seek(-1*(numlines*fmtsize + struct.calcsize("i")),1) #from current location backwards
                        fout.write(struct.pack("i",numlines))
                        fout.seek(numlines*fmtsize,1) #from current location forwards
                    fin.seek(host_loc)
                    if verbose:
                        print time.time()-start, 'Time to read all subhalos'
                except KeyError: #Host with no subs, do nothing
                    pass
            ## else, is a subhalo, which means it will have already been read/written
            else: 
                #skip down to next tree
                while line != '' and line[0:5] != "#tree":
                    line = fin.readline()
            i = i+1
            if i % 5000 == 0 and time_me:
                print i,"host halos completed"
        else:
            line = fin.readline()
    if time_me:
        print time.time()-start, 'Time for conversion'
    fin.close()
    fout.close()
    findex.close()

class MTCatalogueTree:
    """
    Creates a Tree
    Either from an input datatable (e.g. used internally to make subtrees)
    Or from a file that is already pointing to the right place (e.g. from MTCatalogue)
    """
    def __init__(self,scale_list=[],datatable=np.array([]),
                 f=None,halotype=-1,nrow=-1,fmt="",fmttype=np.dtype([])):
        self.scale_list = scale_list
        if datatable != np.array([]):
            self.fileloc = -1
            self.halotype = 2
            self.nrow = len(datatable)
            self.data = datatable
            self.rockstar_id = self.data[0]['origid']
        else:
            if f==None or halotype==-1 or nrow==-1 or fmt=="" or fmttype==np.dtype([]):
                print "ERROR: must specify all of these variables:"
                print "f,halotype,nrow,fmt,fmttype"
                raise RuntimeException("Didn't specify all variables")
            self.fileloc = f.tell()
            self.halotype=halotype #0 or 1
            self.nrow = nrow
            self.data = np.zeros(self.nrow,dtype=fmttype)
            fmtsize = struct.calcsize(fmt)
            for i in xrange(nrow):
                self.data[i] = struct.unpack(fmt,f.read(fmtsize))
            self.rockstar_id = self.data[0]['origid']

    def plottree(self,filename='mytree',makepdf=True,savedot=False,mask=None):
        """
        http://www.graphviz.org/doc/info/attrs.html
        @param filename: the file name you want to save to. Don't put on a file extension,
                         e.g. if you want 'mytree.pdf' then filename='mytree'
        @param makepdf: defaults to True, writes a .ps2 and converts to .pdf using the
                        shell's convert program
        @param savedot: writes out the .dot file. May be useful if your graph is ginormous
                        and takes too long to compute.
        @param mask: UNDER DEVELOPMENT an optional boolean array to mask the tree's data. 
                     Intended for pruning small objects out of gigantic trees when plotting.
                     WILL NOT WORK if you prune a halo from the middle of a branch!
                     (It'll add at least one more halo after the one you want,
                     it won't reconnect halos if you splice one in the middle,
                     and no guarantees that it will work properly even after that.)
                     The user is responsible for doing something that won't break the
                     plotting (i.e., don't get rid of the base halo), and for keeping
                     track of what mask is applied.
                     Note the mask is just for making the plot, i.e. it will not be saved
                     into the tree's internal data structures.
        TODO allow some flexibility in coloring/text? I don't think so, it may be best
             to write more functions that can modify the returned graph object.

        @return graph: the pydot.Dot graph object
        """
        if makepdf and filename[-4:] == '.pdf': filename = filename[:-4]
        if mask != None:
            plotdata = self.data[mask]
        else:
            plotdata = self.data
        print "Generating graph"
        maxvalue = np.max(plotdata['rvir'])

        graph = pydot.Dot(graph_type='graph',size="8, 8")
        for row in reversed(xrange(len(plotdata))):
            nodesize = 100.0*(plotdata[row]['rvir']/maxvalue)
            if nodesize < 0.01: continue #skip over things too small to plot
            graph.add_node(pydot.Node(plotdata[row]['id'],
                                      shape='circle',fixedsize="true",
                                      width=nodesize,#height=nodesize,
                                      label=" "
                                      #label=str(getsnap(plotdata[row]['scale']))+": "+str(plotdata[row]['origid'])
                                      ))
            graph.add_edge(pydot.Edge(plotdata[row]['id'],plotdata[row]['desc_id']))
        #Delete the extra last node
        graph.del_edge(plotdata[0]['id'],plotdata[0]['desc_id'])
        graph.del_node(plotdata[0]['desc_id'])
        if savedot:
            print "Writing dot file"
            graph.write_dot(filename+'.dot')
        if makepdf:
            print "Writing "+str(len(graph.get_nodes()))+" nodes and "+str(len(graph.get_edges()))+" edges to "+filename+'.ps2'
            print "(may freeze/take hours if graph is too big)"
            graph.write_ps2(filename+'.ps2')
            print "Converting to "+filename+'.pdf'
            subprocess.call(["convert",filename+'.ps2',filename+'.pdf'])
            print "Removing "+filename+'.ps2'
            subprocess.call(["rm",filename+'.ps2'])
        return graph

    def getSubTree(self,row):
        """
        Returns a MTCatalogueTree object that is the subtree of the halo specified by row
        Uses depth-first ID to get the subtree
        (and may be a shallow copy of the data, so don't delete the original tree)
        """
        dfid_base = self.data[row]['dfid']
        dfid_last = self.data[row]['lastprog_dfid']
        mask = np.logical_and(self.data['dfid']>=dfid_base, self.data['dfid']<=dfid_last)
        return MTCatalogueTree(scale_list=self.scale_list,datatable=self.data[mask])

    def getMainBranch(self, row=0):
        """
        @param row: row of the halo you want the main branch for. Defaults to row 0
        Uses getSubTree, then finds the smallest dfid that has no progenitors
        @return: all halos that are in the main branch of the halo specified by row (in a np structured array)
        """
        subtree = self.getSubTree(row)
        dfid_base = self.data[row]['dfid'] #==subtree[0]['dfid']
        # Get the smallest dfid of the tree "leaves" (halos with no progenitors)
        dfid_last = np.min(subtree[subtree['num_prog']==0]['dfid'])
        return subtree[np.logical_and(subtree['dfid']>=dfid_base,subtree['dfid']<=dfid_last)]

    def getMMP(self, row):
        """
        @param row: row number (int) of halo considered
        @return: row number of the most massive parent, or None if no parent
        """
        parent = np.where(np.logical_and(self.data[row]['id']==self.data['desc_id'], self.data['mmp']==1))[0]
        try:
            return parent[0]
        except:
            return None # if it has no parent

    def getNonMMPprogenitors(self,row):
        """
        return row index of all progenitors that are not the most massive
        These are all the subhalos that were destroyed in the interval
        """
        return np.where(np.logical_and(self.data[row]['id']==self.data['desc_id'], self.data['mmp']!=1))[0]

    def __getitem__(self,key):
        return self.data[key]

    def __repr__(self):
        return "MTCatalogueTree for RSid: "+str(self.rockstar_id)+", "+str(self.nrow)+" rows."
    
class MTCatalogue:
    """
    Read in the binary file created by convertmt

    Two ways of creating this object.
    The first way is to read in the first N hosts (and their subs).
    Specify numHosts = N (default reads in everything) to read N hosts.
    Also specify indexbyrsid=True to access trees by rsid instead of mass order
    By default trees are accessed by their mass order
    
    The second way is to specify the indexfile (csv file) and a haloid.
    This will use indexfile to pinpoint the location in datafile corresponding
    to haloid and read in that host halo with all the subhalos as the catalogue.
    """

    def __init__(self,dir,haloids=[],oldversion=False,numHosts=np.infty,indexbyrsid=False,verbose=False):
        self.dir = dir
        self.Trees = {} #key: rockstar halo ID; value: MT file
        self.indexbyrsid = indexbyrsid
        self.scale_list = getScaleFactors(dir[0:-6]) #assumes /trees is current
                                                     #folder in dir
        if oldversion:
            self.fmt = "fiiiiifffffiffffffffffffiii"
            self.fmttype = np.dtype([('scale','<f8'),('id','<i8'),('desc_id','<i8'),
                                     ('num_prog','<i8'),('pid','<i8'),('upid','<i8'),
                                     ('mvir','<f8'),('orig_mvir','<f8'),
                                     ('rvir','<f8'),('rs','<f8'),
                                     ('vrms','<f8'),('mmp','<i8'),
                                     ('scale_of_last_MM','<f8'),('vmax','<f8'),
                                     ('posX','<f8'),('posY','<f8'),('posZ','<f8'),
                                     ('pecVX','<f8'),('pecVY','<f8'),('pecVZ','<f8'),
                                     ('Jx','<f8'),('Jy','<f8'),('Jz','<f8'),('spin','<f8'),
                                     ('bfid','<i8'), #breadth first ID
                                     ('dfid','<i8'), #depth first ID
                                     ('origid','<i8')]) #rockstar cat ID
        else:
            self.fmt = "fiiiiiifffffiffffffffffffiiiifffffffffff"
            self.fmttype = np.dtype([('scale','<f8'),('id','<i8'),('desc_id','<i8'),
                                     ('num_prog','<i8'),('pid','<i8'),('upid','<i8'),
                                     ('phantom','<i8'),
                                     ('sam_mvir','<f8'),('mvir','<f8'),
                                     ('rvir','<f8'),('rs','<f8'),
                                     ('vrms','<f8'),('mmp','<i8'),
                                     ('scale_of_last_MM','<f8'),('vmax','<f8'),
                                     ('posX','<f8'),('posY','<f8'),('posZ','<f8'),
                                     ('pecVX','<f8'),('pecVY','<f8'),('pecVZ','<f8'),
                                     ('Jx','<f8'),('Jy','<f8'),('Jz','<f8'),('spin','<f8'),
                                     ('bfid','<i8'), #breadth first ID
                                     ('dfid','<i8'), #depth first ID
                                     ('origid','<i8'), #rockstar cat ID
                                     ('lastprog_dfid','<i8'), #depth first ID last progenitor
                                     ('m200c_all','<f8'),('m200b','<f8'),
                                     ('xoff','<f8'),('voff','<f8'),
                                     ('spin_bullock','<f8'),
                                     ('b_to_a','<f8'),('c_to_a','<f8'),
                                     ('A[x]','<f8'),('A[y]','<f8'),('A[z]','<f8'),
                                     ('T/|U|','<f8')])
        self.fmtsize = struct.calcsize(self.fmt)
        ## NOTE: the reason I have separated the while loops is to speed up
        ## the reading (don't have to call if every single time)
        f = open(dir+"/tree.bin",'rb')
        if haloids==[]:
            if verbose: print "Reading whole catalogue"
            start = time.time()
            tag = f.read(8)
            nhosts = 0
            if indexbyrsid: #index by rsid
                while tag != '' and nhosts <= numHosts:
                    halotype,nrow = struct.unpack("ii",tag)
                    if halotype == 0:
                        nhosts+=1
                        if  nhosts>numHosts:
                            continue
                    thistree = MTCatalogueTree(f=f,scale_list=self.scale_list,halotype=halotype,nrow=nrow,fmt=self.fmt,fmttype=self.fmttype)
                    rsid = thistree.rockstar_id ##use rsid
                    self.Trees[rsid] = thistree 
                    tag = f.read(8)
            else: #index by mass order
                counter = 0
                self.HostLocs = []
                while tag != '' and nhosts <= numHosts:
                    halotype,nrow = struct.unpack("ii",tag)
                    if halotype == 0:
                        nhosts+=1
                        if nhosts>numHosts:
                            continue
                        self.HostLocs.append(counter)
                    thistree = MTCatalogueTree(f=f,scale_list=self.scale_list,halotype=halotype,nrow=nrow,fmt=self.fmt,fmttype=self.fmttype)
                    self.Trees[counter] = thistree ##use counter instead of rsid
                    tag = f.read(8)
                    counter+=1
            if verbose: print "Time to finish reading:",time.time()-start
        else:
            #Read just the host halos and their subs
            reader = csv.reader(open(dir+"/treeindex.csv",'r'))
            index = dict(x for x in reader)
            print "Reading these IDs:",haloids
            if numHosts!=np.infty: print "  Warning: ignoring numHosts variable"
            try:
                file_locs = [int(index[str(x)]) for x in haloids] #raises KeyError if problem
                #Read in tree for host halos
                if ~indexbyrsid:
                    counter=0
                    self.HostLocs = []
                for file_loc,haloid in itertools.izip(file_locs,haloids):
                    f.seek(file_loc)
                    tag = f.read(8)
                    halotype,nrow = struct.unpack("ii",tag)
                    if halotype != 0:
                        print "halotype != 0, instead",halotype
                        raise ValueError
                    hosttree = MTCatalogueTree(f=f,scale_list=self.scale_list,halotype=halotype,nrow=nrow,fmt=self.fmt,fmttype=self.fmttype)
                    rsid = hosttree.rockstar_id
                    if rsid != haloid:
                        print "rsid != haloid"
                        print "rsid",rsid,"; haloid",haloid
                        raise ValueError
                    if indexbyrsid:
                        self.Trees[haloid]=hosttree
                    else:
                        self.Trees[counter]=hosttree
                        self.HostLocs.append(counter)
                        counter+=1
                    tag = f.read(8)
                    if len(tag)==0: continue #last host halo in the list, no subs
                    halotype,nrow = struct.unpack("ii",tag)
                    #Read in trees for all subhalos
                    if indexbyrsid: #index by rsid                        
                        while halotype==1:
                            thistree = MTCatalogueTree(f=f,scale_list=self.scale_list,halotype=halotype,nrow=nrow,fmt=self.fmt,fmttype=self.fmttype)
                            rsid = thistree.rockstar_id ##use rsid
                            self.Trees[rsid] = thistree
                            tag = f.read(8)
                            halotype,nrow = struct.unpack("ii",tag)
                    else: #index by mass order
                        while halotype==1:
                            thistree = MTCatalogueTree(f=f,scale_list=self.scale_list,halotype=halotype,nrow=nrow,fmt=self.fmt,fmttype=self.fmttype)
                            self.Trees[counter] = thistree ##use counter instead of rsid
                            counter+=1
                            tag = f.read(8)
                            halotype,nrow = struct.unpack("ii",tag)
            except KeyError:
                print "ERROR: No halo with this ID in the listed index!"
                print "Did you put in the ID of a host halo? The index Alex made only has host halos"
                print "(Catalogue object is still created but empty)"
            except ValueError:
                print "ERROR: Problem with the index. Did not point to a host halo"
                print "or did not point to a host halo that corresponded to the input halo"
                print "(Catalogue object is still created but empty)"
        f.close()

    def getSubTrees(self,treenum):
        """
        returns list of indices of subhalo trees of tree given by treenum
        """
        if self.indexbyrsid:
            # TODO
            print 'getSubTrees not supported for indexbyrsid yet'
            return 0
        else:
            if self.Trees[treenum].halotype !=0:
                print 'ERROR: input halo not a host'
                return []
            row = treenum+1
            while row<len(mt.Trees) and self.Trees[row].halotype == 1:
                row+=1
            return np.arange(treenum+1, row)

    def __getitem__(self,key):
        return self.Trees[key]

    def __repr__(self):
        out = "MTCatalogue from directory: "+self.dir+"\n"
        out = out + "Number of trees: "+str(len(self.Trees))+"\n"
        if self.indexbyrsid:
            return out+"Indexed by Rockstar halo ids"
        else:
            return out+"Indexed by sequential integers in order of mass"
