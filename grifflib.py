import pylab as plt
from array import array
import numpy as np
from scipy.optimize import curve_fit
from matplotlib import rc
from scipy.optimize import leastsq
from math import *
import numpy.random as nprnd
#import MTCatalogue3 as MTC3

#def getMT3(basepath, numTrees):
#    """
#    Get Merger Tree Catalogue for box, with numTrees # of trees.
#    """
#    #base = rsdir[box-1]
#    return MTC3.MTCatalogue3(basepath + 'tree_0_0_0.dat',numTrees)

def load_matrix_from_file(f):
    """
    This function is to load an ascii format matrix (float numbers separated by
    whitespace characters and newlines) into a numpy matrix object.
 
    f is a file object or a file path.
    """
 
    import types
    import numpy
 
    if type(f) == types.StringType:
        fo = open(f, 'r')
        matrix = load_matrix_from_file(fo)
        fo.close()
        return matrix
    elif type(f) == types.FileType:
        file_content = f.read().strip()
        file_content = file_content.replace('\r\n', ';')
        file_content = file_content.replace('\n', ';')
        file_content = file_content.replace('\r', ';')
 
        return numpy.matrix(file_content)
 
    raise TypeError('f must be a file object or a file name.')
    
def linear_fit(xdata, ydata, ysigma=None):

    """
    Performs a linear fit to data.

    Parameters
    ----------
    xdata : An array of length N.
    ydata : An array of length N.
    sigma : None or an array of length N,
        If provided, it is the standard-deviation of ydata.
        This vector, if given, will be used as weights in the fit.

    Returns
    -------
    a, b   : Optimal parameter of linear fit (y = a*x + b)
    sa, sb : Uncertainties of the parameters
    """
    
    if ysigma is None:
        w = ones(len(ydata)) # Each point is equally weighted.
    else:
        w=1.0/(ysigma**2)

    sw = sum(w)
    wx = w*xdata # this product gets used to calculate swxy and swx2
    swx = sum(wx)
    swy = sum(w*ydata)
    swxy = sum(wx*ydata)
    swx2 = sum(wx*xdata)

    a = (sw*swxy - swx*swy)/(sw*swx2 - swx*swx)
    b = (swy*swx2 - swx*swxy)/(sw*swx2 - swx*swx)
    sa = sqrt(sw/(sw*swx2 - swx*swx))
    sb = sqrt(swx2/(sw*swx2 - swx*swx))

    if ysigma is None:
        chi2 = sum(((a*xdata + b)-ydata)**2)
    else:
        chi2 = sum((((a*xdata + b)-ydata)/ysigma)**2)
    dof = len(ydata) - 2
    rchi2 = chi2/dof
    
    #print 'results of linear_fit:'
    #print '   chi squared = ', chi2
    #print '   degrees of freedom = ', dof
    #print '   reduced chi squared = ', rchi2

    return a, b, sa, sb, rchi2, dof

def general_fit(f, xdata, ydata, p0=None, sigma=None, **kw):
    """
    Pass all arguments to curve_fit, which uses non-linear least squares
    to fit a function, f, to data.  Calculate the uncertaities in the
    fit parameters from the covariance matrix.
    """
    popt, pcov = curve_fit(f, xdata, ydata, p0, sigma, **kw)

    #calculate chi-squared
    if sigma is None or sigma.min() == 0.0:
        chi2 = sum(((f(xdata,*popt)-ydata))**2)
    else:
        chi2 = sum(((f(xdata,*popt)-ydata)/sigma)**2)
    #degrees of freedom
    dof = len(ydata) - len(popt)
    #reduced chi-squared
    rchi2 = chi2/dof
    # The uncertainties are the square roots of the diagonal elements
    punc = np.zeros(len(popt))
    for i in np.arange(0,len(popt)):
        punc[i] = np.sqrt(pcov[i,i])
    return popt, punc, rchi2, dof

def readvariable(filename):
    input_file = open(filename, 'r')
    index = array('d')
    index.fromstring(input_file.read())
    return index

def writevariable(filename,inputarray,vartype):
    output_file = open(filename, 'wb')
    writearray = array(vartype, inputarray)
    writearray.tofile(output_file)
    output_file.close()
    print "Writing to...",filename

def getbinnedxy(x,y,nbins=10):
    x = np.array(x)
    y = np.array(y)
    n, _ = np.histogram(x, bins=nbins)
    sy, _ = np.histogram(x, bins=nbins, weights=y)
    sy2, _ = np.histogram(x, bins=nbins, weights=y*y)
    mean = sy / n
    return (_[1:] + _[:-1])/2,mean

def plotbinnedxy(ax,x,y,labelin='data',nbins=10,color='r'):
    x = np.array(x)
    y = np.array(y)
    n, _ = np.histogram(x, bins=nbins)
    sy, _ = np.histogram(x, bins=nbins, weights=y)
    sy2, _ = np.histogram(x, bins=nbins, weights=y*y)

    mean = sy / n
    std = np.sqrt(sy2/n - mean*mean)
    ax.errorbar((_[1:] + _[:-1])/2, mean, yerr=std, fmt=color,marker='.',capsize=0,linestyle='None',ecolor=color,markerfacecolor=color,label=labelin)
    #ax.errorbar((_[1:] + _[:-1])/2, mean, fmt=color,linestyle='-',linewidth=2,label=labelin)

def getystd(x,y,nbins):
    x = np.array(x)
    y = np.array(y)
    n, _ = np.histogram(x, bins=nbins)
    sy, _ = np.histogram(x, bins=nbins, weights=y)
    sy2, _ = np.histogram(x, bins=nbins, weights=y*y)

    mean = sy / n
    std = np.sqrt(sy2/n - mean*mean)
    return std

def residuals(p, y, x):
    err = y-pval(x,p)
    return err

def func(x, a, b):
    #print 10**x
    #return a + b*(x/10**14)
    #x = 10**x/10**14
    #return a + b*x 
    return a*x + b

def plotbinwithbestfit(ax,x,y,nbins,x0,color='r',linestyle='-',labelin='data',drawline=True,drawpoints=True):
    x = np.array(x)
    y = np.array(y)
    xbin,ybin = getbinnedxy(x,y,nbins)
    std = getystd(x,y,nbins)
    mask = np.isnan(std)
    std[mask] = 0.0
    if std.min() == 0.0:
        popt, punc, rchi2, dof = general_fit(func, xbin, ybin, x0)
    else:
        popt, punc, rchi2, dof = general_fit(func, xbin, ybin, x0,std)

    #print labelin,str('{:.2f}'.format(popt[0])), rchi2
    #print str('{:.2f}'.format(popt[0])) + ' & ' + str('{:.3f}'.format(punc[0])) + ' & ' + str('{:.2f}'.format(popt[1])) + ' & ' + str('{:.3f}'.format(punc[1])) + ' & ' + str('{:.2f}'.format(rchi2))

    #print " a:", '{:.2f}'.format(popt[0]),"+-",'{:.3f}'.format(punc[0]),", b:",'{:.2f}'.format(popt[1]),"+-",'{:.3f}'.format(punc[1])
    
    if drawpoints == True:
        ax.errorbar(xbin, ybin, yerr=std, fmt=color,marker='o',capsize=0,linestyle='None',ecolor=color,markerfacecolor=color,label=labelin)
        
    if drawline == True:
        ax.plot(xbin,func(xbin,popt[0],popt[1]),color=color,linestyle=linestyle,linewidth=3,label=labelin)
    
    return popt[0],punc[0],popt[1],punc[1]

def plotxy(x,y):
    fig = plt.figure(1, figsize=(10.0,10.0))
    plt.plot(x,y)
    plt.show()

def scatterxy(x,y,s=1,c='black',xmin=0.0, xmax=0.0, ymin=0.0, ymax=0.0):
    fig = plt.figure(1, figsize=(10.0,10.0))
    ax=fig.add_subplot(1,1,1)
    ax.scatter(x,y,s=s, c=c)
    if (xmin!=0.0) | (xmax!=0.0) | (ymin!=0.0) | (ymax!=0.0):
        ax.set_xlim([xmin,xmax])
        ax.set_ylim([ymin,ymax])
        plt.show()
        
def create31fig(size,xmin,xmax,ymin,ymax,xlabel,ylabel,title=None):
    fig = plt.figure(figsize=(size,size))
    ax1 = fig.add_subplot(311)
    ax2 = fig.add_subplot(312)
    ax3 = fig.add_subplot(313)
    plt.subplots_adjust(hspace=0.08)
    plt.subplots_adjust(wspace=0.08)
    ax1.set_xticklabels([])
    ax2.set_xticklabels([])
    xticklabels = ax1.get_xticklabels()+ ax2.get_xticklabels()
    plt.setp(xticklabels, visible=False)
    ax1.set_title(title)
    ax2.set_ylabel(ylabel, fontsize = 20)
    ax3.set_xlabel(xlabel, fontsize = 20)
    ax1.set_xlim([xmin,xmax])
    ax2.set_xlim([xmin,xmax])
    ax3.set_xlim([xmin,xmax])
    ax1.set_ylim([ymin,ymax])
    ax2.set_ylim([ymin,ymax])
    ax3.set_ylim([ymin,ymax])
    return fig,ax1,ax2,ax3

def create3x3fig(size,xmin,xmax,ymin,ymax,xlabel,ylabel):
    fig = plt.figure(figsize=(size,size))
    ax1 = fig.add_subplot(331)
    ax2 = fig.add_subplot(332)
    ax3 = fig.add_subplot(333)

    ax4 = fig.add_subplot(334)
    ax5 = fig.add_subplot(335)
    ax6 = fig.add_subplot(336)

    ax7 = fig.add_subplot(337)
    ax9 = fig.add_subplot(339)

    plt.subplots_adjust(hspace=0.05)
    plt.subplots_adjust(wspace=0.05)

    ticklabels = ax1.get_xticklabels() + ax2.get_xticklabels() + ax3.get_xticklabels() + ax4.get_xticklabels() + \
                 ax5.get_xticklabels() + ax6.get_xticklabels() + ax9.get_xticklabels() + \
                 ax1.get_yticklabels() + ax2.get_yticklabels() + ax3.get_yticklabels() + ax4.get_yticklabels() + \
                 ax5.get_yticklabels() + ax6.get_yticklabels() + ax9.get_yticklabels()

    plt.setp(ticklabels, visible=False)

    ax7.set_ylabel(ylabel)
    ax7.set_xlabel(xlabel)

    ax1.set_xlim([xmin,xmax])
    ax3.set_xlim([xmin,xmax])
    ax4.set_xlim([xmin,xmax])
    ax5.set_xlim([xmin,xmax])
    ax6.set_xlim([xmin,xmax])
    ax7.set_xlim([xmin,xmax])
    ax9.set_xlim([xmin,xmax])

    ax1.set_ylim([ymin,ymax])
    ax3.set_ylim([ymin,ymax])
    ax4.set_ylim([ymin,ymax])
    ax5.set_ylim([ymin,ymax])
    ax6.set_ylim([ymin,ymax])
    ax7.set_ylim([ymin,ymax])
    ax9.set_ylim([ymin,ymax])


    return fig,ax1,ax2,ax3,ax4,ax5,ax6,ax7,ax9
    
def drawcircle(x,y,r,vec):
    if vec == True:
        phi = np.linspace(0.0,2*np.pi,100)
        na=np.newaxis
        x_line = x[na,:]+r[na,:]*np.sin(phi[:,na])
        y_line = y[na,:]+r[na,:]*np.cos(phi[:,na])
    if vec == False:
        x = float(x)
        y = float(y)
        r = float(r)
        phi = np.linspace(0.0,2*np.pi,100)
        na=np.newaxis
        x_line = x+r*np.sin(phi)
        y_line = y+r*np.cos(phi)
    return x_line,y_line

def determinebasepath(node):
    if node == "csr-dyn-150.mit.edu":
        basepath = '/Users/griffen/Desktop/'
    if node == "Brendans-MacBook-Pro.local":
        basepath = '/Users/griffen/Desktop/'
    if node == "spacebase":
        basepath = '/spacebase/data/AnnaGroup/'
        
    return basepath

def drawcircle(x,y,r,vec):
    if vec == True:
        phi = np.linspace(0.0,2*np.pi,100)
        na=np.newaxis
        x_line = x[na,:]+r[na,:]*np.sin(phi[:,na])
        y_line = y[na,:]+r[na,:]*np.cos(phi[:,na])
    if vec == False:
        x = float(x)
        y = float(y)
        r = float(r)
        phi = np.linspace(0.0,2*np.pi,100)
        na=np.newaxis
        x_line = x+r*np.sin(phi)
        y_line = y+r*np.cos(phi)
    return x_line,y_line
    
def makelegend(ax,line=0,location=1):
    handles, labels = ax.get_legend_handles_labels()
    
    if len(labels) >3: 
        handles = [h for h in handles]
        labels = [h for h in labels]
        handles = handles[0:3]
        labels = labels[0:3]
    else:
        handles = [h for h in handles]
        labels = [h for h in labels]
    
    if len(labels) >= 2:
        handles[0], handles[1] = handles[1], handles[0]
        labels[0], labels[1] = labels[1], labels[0]

    ax.legend(handles, labels, loc=location,numpoints=1,prop={'size':16})
    # test1.py executed as script
    # do something
