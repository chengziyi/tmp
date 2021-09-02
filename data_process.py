import os
import pickle
import re
import copy
import time
import argparse
from tqdm import tqdm

def process_type_list(list_path = './type_list.txt'):
    '''
    取所有字母和数字，然后保留 字母+数字 的组合
    '''
    with open(list_path, 'r') as f:
        type_list=f.readlines()
    # print(type_list)
    res = []
    match = r'[A-Za-z0-9_-]'
    res=[''.join(re.findall(match, s)) for s in type_list]
    while res.count(''):
        res.remove('')

    res_tmp = copy.copy(res)
    for s in res_tmp:
        tmp = re.findall(r'[A-Za-z]', s)
        tmp2 = re.findall(r'[0-9]', s)
        if tmp == [] or tmp2 == []:
            res.remove(s)

    with open(list_path, 'w') as f:
        for r in res:
            f.writelines(r+'\n')

def process_brand_list(list_path = './brand_list.txt'):
    '''
    中英文分开 尼康(Nikon)->尼康, Nikon
    '''
    with open(list_path, 'r') as f:
        brand_list_tmp=f.readlines()
    brand_list_tmp = list(map(lambda x:x.strip('\n'), brand_list_tmp))
    brand_list = []
    for s in brand_list_tmp:
        tx = re.search(r'[(](.*?)[)]', s)
        if tx is not None:
            brand_en = re.sub('\('+tx.group(1)+'\)', '', s)
            brand_ch = tx.group(1)
            brand_list.extend([brand_en, brand_ch])
        else:
            brand_list.append(s)

    with open(list_path, 'w') as f:
        for r in brand_list:
            f.writelines(r+'\n')

def label_a_str(text_str, item_list, label_type):
    assert label_type in ['BRAD', 'TYPE', 'CATE'], "label_type error"
    label_str = 'O'*len(text_str)

    def match_all(text_str, match_str):
        start_end_list = []
        match=f'({match_str})'
        res=re.finditer(match, text_str)
        for i in range(text_str.count(match_str)):
            try:
                res_iter = next(res)
                start_end_list.append((res_iter.start(), res_iter.end()))
            except:
                break
        return start_end_list

    label_str = list(label_str)
    for match_str in item_list:
        start_end_list = match_all(text_str, match_str)
        for (start, end) in start_end_list:
            label_str[start]='B'+'-'+label_type
            for i in range(start+1, end-1):
                label_str[i]='I'+'-'+label_type
            label_str[end-1]='E'+'-'+label_type

    # label_str = ''.join(label_str)
    return label_str

def label_all_data(data_dir):
    brand_list = []
    with open('./brand_list.txt', 'r') as f:
        brand_list=f.readlines()
    with open('./type_list.txt', 'r') as f:
        type_list=f.readlines()
    with open('./category_list.txt', 'r') as f:
        category_list=f.readlines()
    brand_list = list(map(lambda x:x.strip('\n'), brand_list))
    type_list = list(map(lambda x:x.strip('\n'), type_list))
    category_list = list(map(lambda x:x.strip('\n'), category_list))

    label_res = []
    for file_name in os.listdir(data_dir):
        file_path = os.path.join(data_dir, file_name)
        with open(file_path, 'r') as f:
            text_data = f.readlines()
        if len(text_data)==0:continue
        assert len(text_data)==1
        text_str = text_data[0]
        label_str_brad = label_a_str(text_str, brand_list, 'BRAD')
        label_str_type = label_a_str(text_str, type_list, 'TYPE')
        label_str_cate = label_a_str(text_str, category_list, 'CATE')

        for i in range(len(label_str_brad)):
            if label_str_cate[i]!='O' or label_str_type[i]!='O':
                label_str_brad[i] = label_str_cate[i] if label_str_cate[i]!='O' else label_str_type[i]

        label_res.append((list(text_str), label_str_brad))

    return label_res

def data_sort(file_path):
    '''
    对所有条目，按字符串长度从短到长排序，先匹配短条目再匹配长条目，解决包含关系匹配出错问题，如M1, M1-L213B
    '''
    with open(file_path, 'r') as f:
        data_list = f.readlines()

    res=sorted(data_list, key=lambda x:len(x))
    with open(file_path,'w') as f:
        f.writelines(res)

if __name__ == "__main__":
    # process_type_list()
    # process_brand_list()
    # data_sort('./brand_list.txt')
    # data_sort('./category_list.txt')
    # data_sort('./type_list.txt')

    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir',default=None)
    data_dir = parser.parse_args().data_dir
    if data_dir is None:
        print('input data dir')
        quit()

    t1=time.time()
    res = []
    for dir_name in tqdm(os.listdir(data_dir)):
        dir_path = os.path.join(data_dir, dir_name)
        tmp_res = label_all_data(dir_path)
        res.extend(tmp_res)
    print(f'data len:{len(res)}, use time:{time.time()-t1}')

    final_res = []
    for l1,l2 in res:
        tmp=zip(l1, l2)
        tmp_r=list(map(lambda x:' '.join(x)+'\n', tmp))
        final_res.append(tmp_r)
    # print(final_res)
    for i in final_res:
        i.append('end\n')

    with open('ner_dataset.pkl', 'wb') as f:
        pickle.dump(final_res, f)

