import pandas as pd
import cantools
import datetime
import time
import multiprocessing
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import matplotlib.colors as mcolors


#数据文件路径
asc_file_name='./data/AD002_0730_1645.asc'
#CAN记录仪型号，涉及到不同的数据格式
can_dev='gc'
#需要读取的报文名称
can_sgname_list2=[['VCU_ActualSteeringAngleFB','ADCU_TargetSteeringAngle'],['VCU_VehSpd']]

can_sgname_list=[]
for i in can_sgname_list2:
    for j in i:
        can_sgname_list.append(j)
#print(can_sgname_list)
print("\033[92mRuning!\033[0m")

class Var_x():
    len_num=0
    all_screen_data_len=0
    inum_dict=dict()
    zd=dict()


dbc_load_start=time.time()

can_name_dict=dict()

# 加载dbc文件
db = cantools.db.load_file('ADCAN.dbc')
print('dbc加载时间:',time.time()-dbc_load_start)
ASC_load_start=time.time()

try:
    ASCfile = pd.read_csv(asc_file_name,skiprows=2,encoding="gbk",sep=' ',delimiter=None,header=None,skipinitialspace=True,on_bad_lines='skip')
except:
    print('没有找到',asc_file_name,'文件')

ASCfile.fillna(0, inplace=True)
#print(ASCfile)
print('all_ASCfile_len:',len(ASCfile))
print('ASC加载时间:',time.time()-ASC_load_start)

for message in db.messages:
    # print(f"Message: {message.name}")
    # print(f"ID: {message.frame_id}")
    #print(message.signals)
    for signal in message.signals:
        if signal.name in can_sgname_list:
            if message.name in can_name_dict:
                can_name_dict[message.name].append(signal.name)
            else:
                can_name_dict[message.name]=[signal.name]
#print('can_name_dict:',can_name_dict)
                
#过滤掉DBC文件中缺失的signal
can_sgname_list=[]
for i in can_name_dict:
    for j in can_name_dict[i]:
        can_sgname_list.append(j)

id_dict=dict()
for i in can_name_dict:
    message=db.get_message_by_name(i)
    #print(message,type(message))
    fid=str(message).split(',')[1][3:]
    if len(fid)<8:
        fid=('0'*(8-len(fid))+fid).upper()+'X'
        id_dict[fid]={'can_name_list':can_name_dict[i],'message':message}
#print('id_dict:',id_dict)

if can_dev=='han_yun':
    for i in range(8,-1,-1):
        if i>0:
            ASCfile[i+5]=ASCfile[i]

    df_can_id=ASCfile[1].str.split('\t', expand=True)
    df_time=ASCfile[0].str.split('\t', expand=True)
    #print(df_can_id)
    df_can_id_list=[]
    for i in range(len(df_can_id[0])):
        c_id=df_can_id[0].iloc[i]
        #print(c_id)
        if len(c_id)<9:
            df_can_id_list.append('0'+c_id)
        else:
            df_can_id_list.append(c_id)
    #print(df_can_id_list)
    ASCfile[0]=df_time[0]
    ASCfile[2]=df_can_id_list
    ASCfile[6]=df_can_id[4]

#print(ASCfile)

screen_id_dict=dict()
for i in id_dict:
    #print(ASCfile[2].str.upper())
    #print('i'*8,i)
    filtered_df = ASCfile[ASCfile[2].str.upper()==i]
    #print('filtered_df:')
    #print(filtered_df)

    filtered_df[14]=filtered_df[6]+filtered_df[7]+filtered_df[8]+filtered_df[9]+filtered_df[10]+filtered_df[11]+filtered_df[12]+filtered_df[13]
    #filtered_df[14]=filtered_df.loc[:,6]+filtered_df.loc[:,7]+filtered_df.loc[:,8]+filtered_df.loc[:,9]+filtered_df.loc[:,10]+filtered_df.loc[:,11]+filtered_df.loc[:,12]+filtered_df.loc[:,13]
    screen_id_dict[i]=filtered_df
    #print('filtered_df:',filtered_df[14])

#print('screen_id_dict:',screen_id_dict)

all_id_list=[]
for i in can_sgname_list:
    for j in id_dict:
        if i in id_dict[j]['can_name_list']:
            all_id_list.append(j)
#print('all_id_list:',all_id_list)

for i in all_id_list:
    Var_x.all_screen_data_len+=len(screen_id_dict[i])
#print('all_screen_data_len:',Var_x.all_screen_data_len)

def get_can_id(input):
    for i in id_dict:
        if input in id_dict[i]['can_name_list']:
            return i
    return None

#print(get_can_id('ADCU_BrakeEnable'))

def data_processing(input):
    t_list=[0,0,0]
    inum=0
    #print(get_can_id(input[0]))
    df = pd.DataFrame(columns=['time','value']) 
    dl=[[],[]]
    for index, row in screen_id_dict[get_can_id(input[0])].iterrows():
        # print(row)
        #print('处理数据:',row[14])
        t0=time.time()
        data_str=''

        data_bytes=bytes.fromhex(row[14])
        #print(data_bytes)

        t1=time.time()

        signal_values = id_dict[row[2].upper()]['message'].decode(data_bytes)
        td1=datetime.datetime(1970, 1, 1, hour=23, minute=23, second=0, microsecond=0)
        dt_object = td1+datetime.timedelta(seconds=float(row[0]))
        #print(signal_values)

        t2=time.time()

        #df.loc[len(df)]=[dt_object,signal_values[input[0]]]
        dl[0].append(dt_object)
        dl[1].append(signal_values[input[0]])

        t3=time.time()

        inum+=1
        Var_x.inum_dict[input[2]]=inum
        #print(Var_x.inum_dict)
        # print("\r", end="")
        # print(inum/Var_x.all_screen_data_len*100,'%',end="")

        # t_list[0]=t_list[0]+(t1-t0)
        # t_list[1]=t_list[1]+(t2-t1)
        # t_list[2]=t_list[2]+(t3-t2)

        input[1].put({input[0]:inum})
    #print('t_list:',t_list)
    input[1].put([input[0],dl])


def get_data(input):
    last_data=dict()
    s_time=time.time()
    display_data=dict()

    t1=time.time()
    while 1:
        inum=0
        data=input[1].get()
        #print('get_data:',data)
        
        if type(data)==list:
            last_data[data[0]]=data[1]
            #print(last_data)
            #print('Var_x.len_num:',Var_x.len_num)
            Var_x.len_num+=1
            if Var_x.len_num>=input[0]:
                break
        else:
            for i in data:
                display_data.update(data)
        
        for i in display_data:
            inum+=display_data[i]
        
        print("\r", end="")
        print('数据处理已完成:{:.2f}%'.format(inum/Var_x.all_screen_data_len*100),end="")
    print('数据处理用时：{:.2f}'.format(time.time()-t1))
            
    #print('last_data:',last_data['VCU_VehSpd'])
    #print(last_data['VCU_VehSpd']['time'])
    
    plt.rcParams['font.family'] = 'Heiti TC'
    fig, ax = plt.subplots(figsize=(16,8),nrows=len(can_sgname_list2),ncols=1,sharex=True)
    
    colors=list(mcolors.TABLEAU_COLORS.keys())
    #print('len(can_sgname_list2):',len(can_sgname_list2))
    if len(can_sgname_list2)<2:
        #fig, ax = plt.subplots(figsize=(16,9),dpi=100)
        ax.set_title('数据折线', loc="center", fontsize=22,fontdict={"color":"g"})        
        for i in last_data:
            #print(i)
            #print(last_data[i][1])
            ax.plot(last_data[i][0],last_data[i][1],label=i,marker='.')
    elif len(can_sgname_list2)>=2:
        #fig, ax = plt.subplots(figsize=(16,9),nrows=len(can_sgname_list2),ncols=1,sharex=True)
        fig.suptitle('数据折线图')
        i2=0
        i3=0
        mpl_axes_dict=dict()
        for j in can_sgname_list2:
            for i in j:
                #print(i)
                #print(last_data[i][1])
                #ax.plot(last_data[i][0],last_data[i][1],label=i,marker='.')
                mpl_axes_dict[i] = ax[i2]
                #print('@'*8)
                mpl_axes_dict[i].plot(last_data[i][0], last_data[i][1], color=mcolors.TABLEAU_COLORS[colors[i3]], label=i,marker='.')
                mpl_axes_dict[i].legend()
                mpl_axes_dict[i].grid(True)
                i3+=1
            i2+=1
            mpl_axes_dict=dict()

    plt.show()


if __name__=='__main__':
    pool=multiprocessing.Pool(len(can_sgname_list)+1)

    q=multiprocessing.Manager().Queue()

    n_i=0
    for i in can_sgname_list:
        #print(screen_id_dict[get_can_id(i)])
        #print(i)
        pool.apply_async(data_processing,args=([i,q,n_i],))
        n_i+=1
    pool.apply_async(get_data,args=([len(can_sgname_list),q],))

    pool.close()
    pool.join()

