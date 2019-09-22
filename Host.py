import tkinter as tk
from tkinter import ttk
import eeg2 as eeg
import time
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)

import matplotlib.pyplot as plt
from crossclassvar import gloVar
from crossclassvar2 import gloVar2
import threading
import numpy as np
import mne
from keras.models import Model as kerasmodel
from keras import layers
import sys
import keras.backend.tensorflow_backend as KTF
import tensorflow as tf

# config = tf.ConfigProto()
# config.gpu_options.allow_growth=True
# session = tf.Session(config=config)
# KTF.set_session(session)


L_BAND = 4
H_BAND = 50

sync_flag = 0

quit_flag = 0

headset = None

fig15 = None

EEG = None

lock15 = 1
lock16 = 1

win = tk.Tk()
win.title("Host computer")

def quit_all():
    global quit_flag,headset
    quit_flag = 1
    if headset:
        headset.running =False
    time.sleep(2)
    win.destroy()


def onFrameConfigure(canvas):
    '''Reset the scroll region to encompass the inner frame'''
    canvas.configure(scrollregion=canvas.bbox("all"))

ResultFrame = ttk.LabelFrame(win, text='Classification Result', borderwidth=0)
ResultFrame.grid(column=1, row=1, sticky='NE')
resultlabel0 = ttk.Label(ResultFrame,text="")
resultlabel0.pack()
resultlabel1 = ttk.Label(ResultFrame,text="")
resultlabel1.pack()
ResultFrame_send = ttk.LabelFrame(win, text='Classification Result', borderwidth=0)
ResultFrame_send.grid(column=1, row=2, sticky='NE')
resultlabel4 = ttk.Label(ResultFrame_send,text="")
resultlabel4.pack()

mighty2 = ttk.LabelFrame(win, text='Hybrid Channels Waveforms')
mighty2.grid(column=0, row=1, sticky='WE')

def tstart():
    t1 = threading.Thread(target=click1)
    t_dl = threading.Thread(target=dleeg)
    #t_pltall = threading.Thread(target=plotall)
    t_finalwave = threading.Thread(target=finalwave)

    t1.start()
    t_dl.start()
    #t_pltall.start()
    t_finalwave.start()

a_label = ttk.Button(win, text="Connect", command=tstart)
a_label.grid(column=0, row=0, sticky='WE')

quit_button = ttk.Button(win, text="Quit", command=quit_all)
quit_button.grid(column=1, row=0, sticky='WE')

no_pad = {'pad':0, 'rect':(0,0,0,0)}

def click1():
    global headset
    cy_IO = eeg.ControllerIO()
    cy_IO.setInfo("ioObject", cy_IO)
    cy_IO.setInfo("config", 'outputdata')
    cy_IO.setInfo("verbose", "True")
    cy_IO.setInfo("noweb", "False")
    headset = eeg.EEG(int(6), cy_IO, 'outputdata')
    headset.start()


eeg_list = ['eeg']



fig15 = plt.figure(figsize=(7, 3.5))
axf = plt.axes(xlim=(0,10), ylim=(0,1))

canvas = FigureCanvasTkAgg(fig15, master=mighty2)
canvas.get_tk_widget().grid(column=0, row=1, sticky='WE')


def finalwave():
    import matplotlib.lines as line
    linem = line.Line2D([], [])

    time.sleep(10)
    global axf, lock15, fig15

    def init():
        axf.add_line(linem)
        return linem,

    import matplotlib.animation as animation

    def update(i):
        global EEG
        eeg = EEG[:, 0] - np.min(EEG[:, 0])
        eeg = eeg / np.max(eeg)
        eeg = eeg.squeeze()
        del eeg_list[0]
        eeg_list.append(eeg)

        linem.set_ydata(eeg_list[-1])
        linem.set_xdata(np.arange(0, 512, 1))
        # linem.set_ydata(np.zeros(256))
        return linem,
    ani = animation.FuncAnimation(fig15, update,
                                  frames=1,
                                  init_func=init,
                                  interval=1,
                                  blit=True)
# def plotall():
#     global EEG
#     time.sleep(5)
#     while 1:
#         global quit_flag
#
#         if quit_flag == 1:
#             break
#
#         EEG = gloVar2.npeeg

def dleeg():
    time.sleep(2.5)
    timelist= []
    def filter(EEG_data_block):
        # EEG_data_block = np.array(EEG_data_block).squeeze().T
        # print(EEG_data_block.shape)
        # info = mne.create_info(
        #     ch_names=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',
        #               '13', '14'],
        #     ch_types=['eeg'] * 14,
        #     sfreq=256
        # )
        # raw = mne.io.RawArray(EEG_data_block, info)
        # raw.filter(L_BAND, H_BAND, verbose=False)
        # raw_df = mne.io.RawArray.to_data_frame(raw)
        # raw_df = raw_df.values
        # EEG_data_block = raw_df
        EEG_data_block = EEG_data_block[-256:, :]
        return EEG_data_block

    def reshape(data_train_slice):
        data_train_slice = data_train_slice - np.mean(data_train_slice, axis=0)
        EEG_DEEP = len(data_train_slice)
        EEG_C1 = np.reshape(data_train_slice[:, 0], [1, 1, EEG_DEEP])
        EEG_C2 = np.reshape(data_train_slice[:, 1], [1, 1, EEG_DEEP])
        EEG_C3 = np.reshape(data_train_slice[:, 2], [1, 1, EEG_DEEP])
        EEG_C4 = np.reshape(data_train_slice[:, 3], [1, 1, EEG_DEEP])
        EEG_C5 = np.reshape(data_train_slice[:, 4], [1, 1, EEG_DEEP])
        EEG_C6 = np.reshape(data_train_slice[:, 5], [1, 1, EEG_DEEP])
        EEG_C7 = np.reshape(data_train_slice[:, 6], [1, 1, EEG_DEEP])
        EEG_C8 = np.reshape(data_train_slice[:, 7], [1, 1, EEG_DEEP])
        EEG_C9 = np.reshape(data_train_slice[:, 8], [1, 1, EEG_DEEP])
        EEG_C10 = np.reshape(data_train_slice[:, 9], [1, 1, EEG_DEEP])
        EEG_C11 = np.reshape(data_train_slice[:, 10], [1, 1, EEG_DEEP])
        EEG_C12 = np.reshape(data_train_slice[:, 11], [1, 1, EEG_DEEP])
        EEG_C13 = np.reshape(data_train_slice[:, 12], [1, 1, EEG_DEEP])
        EEG_C14 = np.reshape(data_train_slice[:, 13], [1, 1, EEG_DEEP])
        EEG_0 = np.reshape(np.zeros([EEG_DEEP, 1]), [1, 1, EEG_DEEP])
        colunm_1 = np.concatenate([EEG_0, EEG_0, EEG_C3, EEG_C12, EEG_0, EEG_0], axis=1)
        colunm_2 = np.concatenate([EEG_C4, EEG_0, EEG_C1, EEG_C14, EEG_0, EEG_C11], axis=1)
        colunm_3 = np.concatenate([EEG_0, EEG_C2, EEG_0, EEG_0, EEG_C13, EEG_0], axis=1)
        colunm_4 = np.concatenate([EEG_C5, EEG_0, EEG_0, EEG_0, EEG_0, EEG_C10], axis=1)
        colunm_5 = np.concatenate([EEG_0, EEG_C6, EEG_0, EEG_0, EEG_C9, EEG_0], axis=1)
        colunm_6 = np.concatenate([EEG_0, EEG_0, EEG_C7, EEG_C8, EEG_0, EEG_0], axis=1)
        map = np.concatenate([colunm_1, colunm_2, colunm_3, colunm_4, colunm_5, colunm_6], axis=0)
        map = map.reshape([1,6,6,256])
        return map

    input = layers.Input(shape=(6, 6, 256))
    conv = layers.Reshape([6, 6, 256, 1])(input)
    conv = layers.Conv3D(16, [3, 3, 5], padding='same', strides=[2, 2, 4])(conv)
    conv = layers.BatchNormalization()(conv)
    conv = layers.Activation('elu')(conv)
    conv0 = layers.Conv3D(32, [2, 2, 1], padding='same', strides=[2, 2, 1])(conv)
    conv0 = layers.BatchNormalization()(conv0)
    conv0 = layers.Activation('elu')(conv0)
    conv0 = layers.Conv3D(64, [2, 2, 1], padding='same', strides=[2, 2, 1])(conv0)
    conv0 = layers.BatchNormalization()(conv0)
    conv0 = layers.Activation('elu')(conv0)
    conv0 = layers.Flatten()(conv0)
    conv1 = layers.Conv3D(32, [2, 2, 3], padding='same', strides=[2, 2, 2])(conv)
    conv1 = layers.BatchNormalization()(conv1)
    conv1 = layers.Activation('elu')(conv1)
    conv1 = layers.Conv3D(64, [2, 2, 3], padding='same', strides=[2, 2, 2])(conv1)
    conv1 = layers.BatchNormalization()(conv1)
    conv1 = layers.Activation('elu')(conv1)
    conv1 = layers.Flatten()(conv1)
    conv2 = layers.Conv3D(32, [2, 2, 5], padding='same', strides=[2, 2, 4])(conv)
    conv2 = layers.BatchNormalization()(conv2)
    conv2 = layers.Activation('elu')(conv2)
    conv2 = layers.Conv3D(64, [2, 2, 5], padding='same', strides=[2, 2, 4])(conv2)
    conv2 = layers.BatchNormalization()(conv2)
    conv2 = layers.Activation('elu')(conv2)
    conv2 = layers.Flatten()(conv2)
    conv = layers.Dense(32)(conv0)
    conv = layers.BatchNormalization()(conv)
    conv = layers.Activation('relu')(conv)
    conv = layers.Dense(32)(conv)
    conv = layers.BatchNormalization()(conv)
    conv = layers.Activation('relu')(conv)
    output0 = layers.Dense(2, name='output0')(conv)
    output0 = layers.Activation('softmax')(output0)
    conv = layers.Dense(32)(conv1)
    conv = layers.BatchNormalization()(conv)
    conv = layers.Activation('relu')(conv)
    conv = layers.Dense(32)(conv)
    conv = layers.BatchNormalization()(conv)
    conv = layers.Activation('relu')(conv)
    output1 = layers.Dense(2, name='output1')(conv)
    output1 = layers.Activation('softmax')(output1)
    conv = layers.Dense(32)(conv2)
    conv = layers.BatchNormalization()(conv)
    conv = layers.Activation('relu')(conv)
    conv = layers.Dense(32)(conv)
    conv = layers.BatchNormalization()(conv)
    conv = layers.Activation('relu')(conv)
    output2 = layers.Dense(2, name='output2')(conv)
    output2 = layers.Activation('softmax')(output2)
    r = layers.Add()([output0, output1, output2])
    output = layers.Activation('softmax')(r)
    CNN3D = kerasmodel(input, output0)
    CNN3D.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    print('compiled')
    CNN3D.load_weights('eeg.h5')

    def dlcal(CNN3D,list):
        global lock16, EEG
        lock16 = 1
        unfiltered_eeg = gloVar.npfilter
        filtered_eeg = filter(unfiltered_eeg)
        EEG = unfiltered_eeg
        print('EEEEGEGEGEGEGEG')
        print(EEG.shape)
        reshaped_eeg = reshape(filtered_eeg)
        result = CNN3D.predict(reshaped_eeg, 1)
        result = result.squeeze()
        resultlabel0.configure(text=str(round(result[0] * 100, 2)))
        resultlabel1.configure(text=str(round(result[1] * 100, 2)))
        list.append(result)
        lock16 = 0
    result_final = []
    notsend = None
    global lock16

    # import socket
    # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.connect(('192.168.0.110', 8000))

    while 1:
        global quit_flag
        if quit_flag == 1:
            # sock.send(bytes('+', encoding='utf-8'))
            # sock.close()
            break

        starttime = time.time()
        tdl = threading.Thread(target=dlcal(CNN3D, result_final))
        tdl.start()

        if len(result_final) == 5:
            while 1:
                if lock16 == 0:
                    break
            for r in range(len(result_final)-1):
                if np.argmax(result_final[r]) == np.argmax(result_final[r+1]):
                    notsend = False
                    continue
                else:
                    notsend = True
                    resultlabel4.configure(text='Not Sended')
                    print('nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn')
                    break
            if not notsend:
                resultlabel4.configure(text=str(np.argmax(result_final[-1])+1))
                # sock.send(bytes(str(np.argmax(result_final[-1])+1), encoding='utf-8'))
                print('ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss')

            result_final = result_final[-4:]
        else:
            while 1:
                if lock16 == 0:
                    break
            continue

        endtime = time.time()
        print('Running time: %s Seconds' % (endtime - starttime))
        timelist.append((endtime - starttime))
        if len(timelist) >500:
            print('AVERAGE:')
            print(np.min(np.array(timelist[:500])))


win.mainloop()
sys.exit()