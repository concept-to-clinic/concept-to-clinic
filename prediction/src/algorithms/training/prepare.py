import os
import shutil
import warnings
import sys
sys.path.append('../preprocessing')

from multiprocessing import Pool
from functools import partial
from os import path as p

import numpy as np
import h5py
import pandas
import scipy
import SimpleITK as sitk

from scipy.io import loadmat
from scipy.ndimage.interpolation import zoom
from scipy.ndimage.morphology import binary_dilation, generate_binary_structure
from skimage import measure
from skimage.morphology import convex_hull_image

from step1 import step1_python
from config_training import config

def resample(imgs, spacing, new_spacing,order=2):
    if len(imgs.shape)==3:
        new_shape = np.round(imgs.shape * spacing / new_spacing)
        true_spacing = spacing * imgs.shape / new_shape
        resize_factor = new_shape / imgs.shape
        imgs = zoom(imgs, resize_factor, mode = 'nearest',order=order)
        return imgs, true_spacing
    elif len(imgs.shape)==4:
        n = imgs.shape[-1]
        newimg = []
        for i in range(n):
            slice = imgs[:,:,:,i]
            newslice,true_spacing = resample(slice,spacing,new_spacing)
            newimg.append(newslice)
        newimg=np.transpose(np.array(newimg),[1,2,3,0])
        return newimg,true_spacing
    else:
        raise ValueError('wrong shape')
def worldToVoxelCoord(worldCoord, origin, spacing):

    stretchedVoxelCoord = np.absolute(worldCoord - origin)
    voxelCoord = stretchedVoxelCoord / spacing
    return voxelCoord

def load_itk_image(filename):
    with open(filename) as f:
        contents = f.readlines()
        line = [k for k in contents if k.startswith('TransformMatrix')][0]
        transformM = np.array(line.split(' = ')[1].split(' ')).astype('float')
        transformM = np.round(transformM)
        if np.any( transformM!=np.array([1,0,0, 0, 1, 0, 0, 0, 1])):
            isflip = True
        else:
            isflip = False

    itkimage = sitk.ReadImage(filename)
    numpyImage = sitk.GetArrayFromImage(itkimage)

    numpyOrigin = np.array(list(reversed(itkimage.GetOrigin())))
    numpySpacing = np.array(list(reversed(itkimage.GetSpacing())))

    return numpyImage, numpyOrigin, numpySpacing,isflip

def process_mask(mask):
    convex_mask = np.copy(mask)
    for i_layer in range(convex_mask.shape[0]):
        mask1  = np.ascontiguousarray(mask[i_layer])
        if np.sum(mask1)>0:
            mask2 = convex_hull_image(mask1)
            if np.sum(mask2)>1.5*np.sum(mask1):
                mask2 = mask1
        else:
            mask2 = mask1
        convex_mask[i_layer] = mask2
    struct = generate_binary_structure(3,1)
    dilatedMask = binary_dilation(convex_mask,structure=struct,iterations=10)
    return dilatedMask


def lumTrans(img):
    lungwin = np.array([-1200.,600.])
    newimg = (img-lungwin[0])/(lungwin[1]-lungwin[0])
    newimg[newimg<0]=0
    newimg[newimg>1]=1
    newimg = (newimg*255).astype('uint8')
    return newimg


def savenpy(id,annos,filelist,data_path,prep_folder):
    resolution = np.array([1,1,1])
    name = filelist[id]
    print 'data_path:', data_path
    label = annos[annos[:,0]==name]
    label = label[:,[3,1,2,4]].astype('float')

    im, m1, m2, spacing = step1_python(p.join(data_path,name))
    Mask = m1 + m2

    newshape = np.round(np.array(Mask.shape)*spacing/resolution)
    xx,yy,zz= np.where(Mask)
    box = np.array([[np.min(xx),np.max(xx)],[np.min(yy),np.max(yy)],[np.min(zz),np.max(zz)]])
    box = box*np.expand_dims(spacing,1)/np.expand_dims(resolution,1)
    box = np.floor(box).astype('int')
    margin = 5
    extendbox = np.vstack([np.max([[0,0,0],box[:,0]-margin],0),np.min([newshape,box[:,1]+2*margin],axis=0).T]).T
    extendbox = extendbox.astype('int')

    convex_mask = m1
    dm1 = process_mask(m1)
    dm2 = process_mask(m2)
    dilatedMask = dm1+dm2
    Mask = m1+m2
    extramask = dilatedMask - Mask
    bone_thresh = 210
    pad_value = 170
    im[np.isnan(im)]=-2000
    sliceim = lumTrans(im)
    sliceim = sliceim*dilatedMask+pad_value*(1-dilatedMask).astype('uint8')
    bones = sliceim*extramask>bone_thresh
    sliceim[bones] = pad_value
    sliceim1,_ = resample(sliceim,spacing,resolution,order=1)
    sliceim2 = sliceim1[extendbox[0,0]:extendbox[0,1],
                extendbox[1,0]:extendbox[1,1],
                extendbox[2,0]:extendbox[2,1]]
    sliceim = sliceim2[np.newaxis,...]
    np.save(p.join(prep_folder,name+'_clean.npy'),sliceim)


    if len(label)==0:
        label2 = np.array([[0,0,0,0]])
    elif len(label[0])==0:
        label2 = np.array([[0,0,0,0]])
    elif label[0][0]==0:
        label2 = np.array([[0,0,0,0]])
    else:
        haslabel = 1
        label2 = np.copy(label).T
        label2[:3] = label2[:3][[0,2,1]]
        label2[:3] = label2[:3]*np.expand_dims(spacing,1)/np.expand_dims(resolution,1)
        label2[3] = label2[3]*spacing[1]/resolution[1]
        label2[:3] = label2[:3]-np.expand_dims(extendbox[:,0],1)
        label2 = label2[:4].T
    np.save(p.join(prep_folder,name+'_label.npy'),label2)

    print(name)

def full_prep(step1=True, step2=True):
    warnings.filterwarnings("ignore")

    #preprocess_result_path = './prep_result'
    prep_folder = config['preprocess_result_path']
    data_path = config['stage1_data_path']
    finished_flag = '.flag_prepkaggle'

    if not p.exists(finished_flag):
        alllabelfiles = config['stage1_annos_path']
        tmp = []
        for f in alllabelfiles:
            content = np.array(pandas.read_csv(f))
            content = content[content[:,0]!=np.nan]
            tmp.append(content[:,:5])
        alllabel = np.concatenate(tmp,0)
        filelist = os.listdir(config['stage1_data_path'])

        if not p.exists(prep_folder):
            os.mkdir(prep_folder)
        #eng.addpath('preprocessing/',nargout=0)

        print('starting preprocessing')
        pool = Pool()
        filelist = os.listdir(data_path)
        partial_savenpy = partial(savenpy,annos= alllabel,filelist=filelist,data_path=data_path,prep_folder=prep_folder )

        N = len(filelist)
            #savenpy(1)
        _ = pool.map(partial_savenpy,range(N))
        pool.close()
        pool.join()
        print('end preprocessing')

    f= open(finished_flag,"w+")

def savenpy_luna(id,annos,filelist,luna_segment,luna_data,savepath):
    islabel = True
    isClean = True
    resolution = np.array([1,1,1])
#     resolution = np.array([2,2,2])
    name = filelist[id]

    Mask,origin,spacing,isflip = load_itk_image(p.join(luna_segment,name+'.mhd'))
    if isflip:
        Mask = Mask[:,::-1,::-1]
    newshape = np.round(np.array(Mask.shape)*spacing/resolution).astype('int')
    m1 = Mask==3
    m2 = Mask==4
    Mask = m1+m2

    xx,yy,zz= np.where(Mask)
    box = np.array([[np.min(xx),np.max(xx)],[np.min(yy),np.max(yy)],[np.min(zz),np.max(zz)]])
    box = box*np.expand_dims(spacing,1)/np.expand_dims(resolution,1)
    box = np.floor(box).astype('int')
    margin = 5
    extendbox = np.vstack([np.max([[0,0,0],box[:,0]-margin],0),np.min([newshape,box[:,1]+2*margin],axis=0).T]).T

    this_annos = np.copy(annos[annos[:,0]==int(name)])

    if isClean:
        convex_mask = m1
        dm1 = process_mask(m1)
        dm2 = process_mask(m2)
        dilatedMask = dm1+dm2
        Mask = m1+m2
        extramask = dilatedMask ^ Mask
        bone_thresh = 210
        pad_value = 170

        sliceim,origin,spacing,isflip = load_itk_image(p.join(luna_data,name+'.mhd'))
        if isflip:
            sliceim = sliceim[:,::-1,::-1]
            print('flip!')
        sliceim = lumTrans(sliceim)
        sliceim = sliceim*dilatedMask+pad_value*(1-dilatedMask).astype('uint8')
        bones = (sliceim*extramask)>bone_thresh
        sliceim[bones] = pad_value

        sliceim1,_ = resample(sliceim,spacing,resolution,order=1)
        sliceim2 = sliceim1[extendbox[0,0]:extendbox[0,1],
                    extendbox[1,0]:extendbox[1,1],
                    extendbox[2,0]:extendbox[2,1]]
        sliceim = sliceim2[np.newaxis,...]
        np.save(p.join(savepath,name+'_clean.npy'),sliceim)


    if islabel:

        this_annos = np.copy(annos[annos[:,0]==int(name)])
        label = []
        if len(this_annos)>0:

            for c in this_annos:
                pos = worldToVoxelCoord(c[1:4][::-1],origin=origin,spacing=spacing)
                if isflip:
                    pos[1:] = Mask.shape[1:3]-pos[1:]
                label.append(np.concatenate([pos,[c[4]/spacing[1]]]))

        label = np.array(label)
        if len(label)==0:
            label2 = np.array([[0,0,0,0]])
        else:
            label2 = np.copy(label).T
            label2[:3] = label2[:3]*np.expand_dims(spacing,1)/np.expand_dims(resolution,1)
            label2[3] = label2[3]*spacing[1]/resolution[1]
            label2[:3] = label2[:3]-np.expand_dims(extendbox[:,0],1)
            label2 = label2[:4].T
        np.save(p.join(savepath,name+'_label.npy'),label2)

    print(name)

def preprocess_luna():
    luna_segment = config['luna_segment']
    savepath = config['preprocess_result_path']
    luna_data = config['luna_data']
    luna_label = config['luna_label']
    finished_flag = '.flag_preprocessluna'
    print('starting preprocessing luna')
    if not p.exists(finished_flag):
        filelist = [f.split('.mhd')[0] for f in os.listdir(luna_data) if f.endswith('.mhd') ]
        annos = np.array(pandas.read_csv(luna_label))

        if not p.exists(savepath):
            os.mkdir(savepath)


        pool = Pool()
        partial_savenpy_luna = partial(savenpy_luna,annos=annos,filelist=filelist,
                                       luna_segment=luna_segment,luna_data=luna_data,savepath=savepath)

        N = len(filelist)
        #savenpy(1)
        _=pool.map(partial_savenpy_luna,range(N))
        pool.close()
        pool.join()
    print('end preprocessing luna')
    f= open(finished_flag,"w+")

def prepare_luna():
    print('start changing luna name')
    luna_raw = config['luna_raw']
    luna_abbr = config['luna_abbr']
    luna_data = config['luna_data']
    luna_segment = config['luna_segment']
    finished_flag = '.flag_prepareluna'

    if not p.exists(finished_flag):

        subsetdirs = [
            p.join(luna_raw,f)
            for f in os.listdir(luna_raw)
            if f.startswith('subset') and p.isdir(p.join(luna_raw,f))]

        if not p.exists(luna_data):
            os.mkdir(luna_data)

        # allnames = []
        # for d in subsetdirs:
        #     files = os.listdir(d)
        #     names = [f[:-4] for f in files if f.endswith('mhd')]
        #     allnames = allnames + names
        # allnames = np.array(allnames)
        # allnames = np.sort(allnames)

        # ids = np.arange(len(allnames)).astype('str')
        # ids = np.array(['0'*(3-len(n))+n for n in ids])
        # pds = pandas.DataFrame(np.array([ids,allnames]).T)
        # namelist = list(allnames)

        abbrevs = np.array(pandas.read_csv(config['luna_abbr'],header=None))
        namelist = list(abbrevs[:, 1])
        ids = abbrevs[:, 0]

        for d in subsetdirs:
            files = os.listdir(d)
            files.sort()
            for f in files:
                name = f[:-4]
                id = ids[namelist.index(name)]
                filename = '0'*(3-len(str(id)))+str(id)
                shutil.move(p.join(d,f),p.join(luna_data,filename+f[-4:]))
                print(p.join(luna_data,str(id)+f[-4:]))

        files = [f for f in os.listdir(luna_data) if f.endswith('mhd')]
        for file in files:
            with open(p.join(luna_data,file),'r') as f:
                content = f.readlines()
                id = file.split('.mhd')[0]
                filename = '0'*(3-len(str(id)))+str(id)
                content[-1]='ElementDataFile = '+filename+'.raw\n'
                print(content[-1])
            with open(p.join(luna_data,file),'w') as f:
                f.writelines(content)


        seglist = os.listdir(luna_segment)

        for f in seglist:
            if f.endswith('.mhd'):

                name = f[:-4]
                lastfix = f[-4:]
            else:
                name = f[:-5]
                lastfix = f[-5:]
            if name in namelist:
                id = ids[namelist.index(name)]
                filename = '0' * (3 - len(str(id))) + str(id)

                shutil.move(p.join(luna_segment,f),p.join(luna_segment,filename+lastfix))
                print(p.join(luna_segment,filename+lastfix))


        files = [f for f in os.listdir(luna_segment) if f.endswith('mhd')]

        for file in files:
            with open(p.join(luna_segment,file),'r') as f:
                content = f.readlines()
                id = file.split('.mhd')[0]
                filename = '0'*(3-len(str(id)))+str(id)
                content[-1] = 'ElementDataFile = ' + filename + '.zraw\n'
                print(content[-1])

            with open(p.join(luna_segment,file),'w') as f:
                f.writelines(content)

    print('end changing luna name')
    f = open(finished_flag,"w+")

def split_samples(all_samples, val_percent):
    train_samples = []
    val_samples = []
    valsplit = (int) (len(all_samples) * val_percent)
    trainsplit = len(all_samples) - valsplit
    target = range(len(all_samples))
    # prepare training samples
    for i in range(trainsplit):
        chosenidx = np.random.choice(np.arange(len(target)))
        train_samples.append(all_samples[chosenidx])
        # remove the case from all_samples
        target.pop(chosenidx)
        all_samples = np.delete(all_samples, chosenidx)

    # prepare validation samples
    target = range(len(all_samples))
    for i in range(valsplit):
        chosenidx = np.random.choice(np.arange(len(target)))
        val_samples.append(all_samples[chosenidx])
        # remove the case from all_samples
        target.pop(chosenidx)
        all_samples = np.delete(all_samples, chosenidx)

    return train_samples, val_samples

def make_symbolic_links(samples, series_paths, symlink_path):
    for series in samples:
        rows, cols = np.where(series_paths == series)
        if rows.size == 0:
            print series, 'not found'
            continue
        series_path = series_paths[rows][0]
        series_abspath = series_path[1]
        link = os.path.join(symlink_path, series)
        if not os.path.exists(link):
            os.symlink(series_abspath, link)

#Example custom dataset: NSCLC-Radiomics(lung1)
#  LUNG1-001
#    (StudyInstanceUID)
#    1.3.6.1.4.1.32722.99.99.239341353911714368772597187099978969331
#      (SeriesInstanceUID)
#      1.3.6.1.4.1.32722.99.99.240801210441213358525710685943800395085
#        000000.dcm (only one file)
#      1.3.6.1.4.1.32722.99.99.298991776521342375010861296712563382046
#        000000.dcm ~ 000133.dcm
def full_prep_custom():
    if not 'custom_data' in config:
        return

    custom_data = config['custom_data']
    prep_folder = config['preprocess_result_path']
    finished_flag = '.flag_prepcustom'
    val_percent = 0.15

    # TODO: add cases here that fail due to inability to extract lung mask from CT scan.
    black_list = []

    if not os.path.isdir(custom_data):
        return

    # collect series ids and their absolute paths
    series_paths = []
    print('reading custom data from: ' + custom_data + '\n------\n' + str(sorted(os.listdir(custom_data))) + '\n------\n')
    for patient in sorted(os.listdir(custom_data)):
        patient_path = os.path.join(custom_data, patient)
        if not os.path.isdir(patient_path):
            continue
        for study in sorted(os.listdir(patient_path)):
            study_path = os.path.join(patient_path, study)
            if not os.path.isdir(study_path):
                continue
            for series in sorted(os.listdir(study_path)):
                if series in black_list:
                    continue
                series_path = os.path.join(study_path, series)
                filelist = [f for f in os.listdir(series_path)]
                if len(filelist) != 1:    # to skip series that only contain one dcm file
                    series_paths.append([series, series_path])

    # save series ids
    series_paths = np.array(series_paths)
    all_samples = series_paths[:, 0]
    # split samples into training and validation samples according val_percent
    custom_train, custom_val = split_samples(all_samples, val_percent)

    # temporarily used for pre-processing
    print('making symbolic links')
    symlink_path = './custom_data/'
    if not os.path.exists(symlink_path):
        os.mkdir(symlink_path)
    make_symbolic_links(all_samples, series_paths, symlink_path)

    print('saving training and validation cases')
    # to use custom dataset for detector training,
    # the 'kaggleluna_full.npy' and 'valsplit.npy' in detector/main.py needs to be replaced as well
    np.save('./detector/custom_train.npy', custom_train)
    np.save('./detector/custom_val.npy', custom_val)

    # to use custom dataset for classifier training,
    # the 'kaggleluna_full.npy' and 'valsplit.npy' in classifier/main.py needs to be replaced as well
    np.save('./classifier/custom_train.npy', custom_train)
    np.save('./classifier/custom_val.npy', custom_val)

    # prepare label file here and replace the 'full_label.csv' in ./classifier/

    if not os.path.exists(finished_flag):
        alllabelfiles = config['custom_annos_path']
        tmp = []
        for f in alllabelfiles:
            content = np.array(pandas.read_csv(f))
            content = content[content[:,0]!=np.nan]
            tmp.append(content[:,:5])
        alllabel = np.concatenate(tmp,0)

        if not p.exists(prep_folder):
            os.mkdir(prep_folder)

        print('start preprocessing custom data')
        pool = Pool()
        partial_savenpy = partial(savenpy,annos= alllabel,filelist=all_samples,data_path=symlink_path,prep_folder=prep_folder )

        N = len(all_samples)
            #savenpy(1)
        _ = pool.map(partial_savenpy,range(N))
        pool.close()
        pool.join()
        print('end preprocessing custom data')

    # we are done with the symbolic links
    print('removing symbolic links')
    for series in all_samples:
        os.remove(os.path.join(symlink_path, series))
    os.rmdir(symlink_path)

    f= open(finished_flag,"w+")

if __name__=='__main__':
    full_prep(step1=True,step2=True)
    prepare_luna()
    preprocess_luna()
    full_prep_custom()

