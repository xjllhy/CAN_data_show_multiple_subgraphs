import pandas as pd
import cantools
import datetime
import time
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


print("\033[92mRuning!\033[0m")

def read_dbc(can_sgname_list2):
    can_sgname_list=[]
    for i in can_sgname_list2:
        for j in i:
            can_sgname_list.append(j)
    #print(can_sgname_list)

    db = cantools.db.load_file('ADCAN.dbc')

    can_name_dict=dict()

    for message in db.messages:
        #print(f"Message: {message.name}")
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
        #print('message:',message,type(message))
        fid=message.frame_id.to_bytes(4, byteorder='big').hex().upper()+'X'
        id_dict[fid]={'can_name_list':can_name_dict[i],'message':message}
    #print('id_dict:',id_dict)
    return id_dict

def generate_list(asc_file_name,offset_time=[0,0,0,0]):
    ASC_load_start=time.time()
    try:
        ASCfile = pd.read_csv(asc_file_name,skiprows=2,encoding="gbk",sep=' ',delimiter=None,header=None,skipinitialspace=True,on_bad_lines='skip')
        ASCfile[0] = pd.to_datetime(ASCfile[0], unit='s')
        ASCfile[0] = ASCfile[0] + pd.DateOffset(years=offset_time[0]) + pd.DateOffset(months=offset_time[1]) + pd.to_timedelta(offset_time[2], unit='d') + pd.to_timedelta(offset_time[3], unit='h')
    except:
        print('没有找到',asc_file_name,'文件')

    ASCfile.fillna(0, inplace=True)
    #print(ASCfile)
    # print('all_ASCfile_len:',len(ASCfile))
    print('ASC加载时间:',time.time()-ASC_load_start)
    return ASCfile.values.tolist()

if __name__ == '__main__':
    can_sgname_list2=[['ADCU_TargetSteeringAngle','VCU_ActualSteeringAngleFB'],['ADCU_SteeringEnable']]
    id_dict=read_dbc(can_sgname_list2)

    asc_file_name='./data/15-00.asc'
    data_list=generate_list(asc_file_name,[50,1,2,3])

    processing_data_start=time.time()
    data_dict=dict()
    i_num=0
    for row in data_list:
        #print(row[2])
        if row[2].upper() in id_dict:
            data_bytes=bytes.fromhex(row[-8]+row[-7]+row[-6]+row[-5]+row[-4]+row[-3]+row[-2]+row[-1])
            signal_values = id_dict[row[2].upper()]['message'].decode(data_bytes)
            #print(signal_values)
            #print(id_dict[row[2].upper()])

            for i in id_dict[row[2].upper()]['can_name_list']:
                #print(i,signal_values[i])
                if i in data_dict:
                    data_dict[i][0].append(row[0])
                    data_dict[i][1].append(signal_values[i])
                else:
                    data_dict[i]=([[row[0]], [signal_values[i]]])
        i_num+=1
        print("\r", end="")
        print('数据处理已完成:{:.2f}%'.format(i_num/len(data_list)*100),end="")
    #print(data_dict)
    print('数据处理时间:',time.time()-processing_data_start)

    plt.rcParams['font.family'] = 'Heiti TC'
    fig, ax = plt.subplots(figsize=(16,8),nrows=len(can_sgname_list2),ncols=1,sharex=True)
    
    colors=list(mcolors.TABLEAU_COLORS.keys())
    #print('len(can_sgname_list2):',len(can_sgname_list2))
    if len(can_sgname_list2)<2:
        #fig, ax = plt.subplots(figsize=(16,9),dpi=100)
        ax.set_title('数据折线', loc="center", fontsize=22,fontdict={"color":"g"})        
        for i in data_dict:
            #print(i)
            #print(last_data[i][1])
            ax.plot(data_dict[i][0],data_dict[i][1],label=i,marker='.')
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
                # print('@'*8)
                # print(data_dict[i][0], data_dict[i][1],)
                mpl_axes_dict[i].plot(data_dict[i][0], data_dict[i][1], color=mcolors.TABLEAU_COLORS[colors[i3]], label=i,marker='.')
                mpl_axes_dict[i].legend()
                mpl_axes_dict[i].grid(True)
                i3+=1
            i2+=1
            mpl_axes_dict=dict()

    plt.show()