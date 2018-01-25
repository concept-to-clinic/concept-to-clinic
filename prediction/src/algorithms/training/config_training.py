config = {
    'stage1_data_path': 's3://dd-stage1/stage1/',
    'luna_raw': 's3://dd-luna/',
    'preprocess_result_path':'/home/ubuntu/kaggle_dataset/concept-to-clinic/prediction/src/algorithms/training/training_prep',
    'luna_segment': 's3://dd-luna/seg-lungs-LUNA16/',
    'luna_data': 's3://dd-luna/allset',
    'luna_abbr': './detector/labels/shorter.csv',
    'luna_label': './detector/labels/lunaqualified.csv',
    'stage1_annos_path': [
        './detector/labels/label_job5.csv',
        './detector/labels/label_job4_2.csv',
        './detector/labels/label_job4_1.csv',
        './detector/labels/label_job0.csv',
        './detector/labels/label_qualified.csv'],
    'custom_data': '/home/ubuntu/TCIA_dataset/NSCLC-Radiomics_Genomics_lung3/',
    'custom_annos_path': [
        '/home/ubuntu/kaggle_dataset/grt123-DSB2017/NSCLC-Radiomics_Genomics(lung3)_annotations.csv'],
    'bbox_path': '../detector/results/res18/bbox/',
    'preprocessing_backend': 'python'
}
