import os
import json
import pdb
import datetime
import sys
import serial
import time


def getPrevious():
    with open('/root/src2/preValue.txt') as f:
        line = f.read().strip()
    try:
        return int(line)
    except:
        return 0


def getCount():
    with open('/root/src2/cnt.txt') as f:
        line = f.read().strip()
    try:
        return int(line)
    except:
        return 0


def writeCount():
    file_path = "/root/src2/cnt.txt"
    try:
        with open(file_path, 'w') as file:
            file.write('0')
        print(f"{file_path}の内容を0に設定しました。")
    except Exception as e:
        print(f"ファイルの書き込みに失敗しました: {e}")


def getHantei(preValue, volt, cnt):
    #    pdb.set_trace()
    #    print(f"cnt is {cnt}")
    #    print(f"preValue is {preValue}")
    #    print(f"volt is {volt}")

    if int(preValue) == int(volt):
        #        print("--------------------------------------------")
        cnt += 1
    else:
        print("--------------------------------------------")
        print("koko derutoki aruno?")
        print(f"preValuje is {preValue}")
        print(f"preCnt is {cnt}")
        print(f"now volt is {volt}")
        print("--------------------------------------------")
        cnt = 0

    if cnt <= 1000 and volt > 15:
        return 0, volt, cnt
    elif cnt <= 1000 and volt < 2:
        #    elif cnt <= 45000 and volt < 2:
        return 0, volt, cnt

    elif cnt > 45000 and volt < 2:
        #    elif cnt > 1000 and volt < 2:
        # koko ni shutdown command
        ser = serial.Serial("/dev/ttyS0", baudrate=230400,
                            timeout=2.5,
                            parity=serial.PARITY_NONE,
                            bytesize=serial.EIGHTBITS,
                            stopbits=serial.STOPBITS_TWO
                            )
        data = {}
        data["cmd"] = "poweroff"
        data["arg"] = 30

        data = json.dumps(data)
        a = data + "\n"

# 2024_07_03 writeCount()実装
        writeCount()
#        time.sleep(2)
#        os.system("systemctl stop auto")
#        time.sleep(2)
#        os.system("/root/app/cui/control/build/control -f poweroff:30:10 -p /dev/ttyS0")
#        time.sleep(2)
        if ser.isOpen():
            ser.write(a.encode('ascii'))
            ser.flush()
            os.system("shutdown -h now")

        return 1, volt, cnt
#        return 0,volt,cnt
# 2024_07_18 ソレノイドオフから10s以降は間引きデータを描画
    elif cnt > 1000 and volt < 2:
        if cnt % 100 == 0:
            return 0, volt, cnt
        else:
            return 1, volt, cnt
    elif cnt > 1000 and volt > 15:
        if cnt % 100 == 0:
            return 0, volt, cnt
        else:
            return 1, volt, cnt
    else:
        print('----------')
        print("kore detya dame dayo?")
        return 0, volt, cnt
        sys.exit()


if _name_ == '__main__':
    now = datetime.datetime.now()
    date_time = now.strftime("%Y_%m_%d_%H_%M_%S")
    SRC_DIR = '/root/src'
    DST_DIR = '/root/src2'
    PREFIX = 'taiwan_'
    # init
    if not os.path.exists(os.path.join(DST_DIR, 'preValue.txt')):
        print("koreha saisyono ikkaidake")
        with open(os.path.join(DST_DIR, 'preValue.txt'), 'w') as f:
            # f.write("24\n")
            f.write("0\n")
    if not os.path.exists(os.path.join(DST_DIR, 'cnt.txt')):
        print("koreha saisyono ikkaidake")
        with open(os.path.join(DST_DIR, 'cnt.txt'), 'w') as f:
            f.write("0\n")

#    pdb.set_trace()

    # gaibu kara preValue kaisyuu
    preValue = getPrevious()
    cnt = getCount()
    print(f"preCnt is {cnt}")
    print(type(cnt))
    print(f"preValue is {preValue}")
    print(type(preValue))
    g_volt = 0
    g_cnt = cnt
    print(f"preCnt is {g_cnt}")
    tmp = 0

    files = os.listdir(SRC_DIR)
    files = sorted([file for file in files if file.startswith(PREFIX)])

    for file in files:
        with open(os.path.join(SRC_DIR, file)) as f:
            lines = f.readlines()

        for line in lines:
            if line != '\n':
                line = line.replace("'", '"')
                try:
                    line = json.loads(line)
                    volt = line.get('volt')
                    g_volt = line.get('volt')

                    if volt is not None:
                        if volt > 15000:
                            volt = 24
                            g_volt = 24
                        else:
                            volt = 0
                            g_volt = 0
#                        hantei,volt,cnt = getHantei(preValue,volt,cnt)
                        hantei, volt, cnt = getHantei(preValue, g_volt, g_cnt)
                        preValue = volt
                        g_cnt = cnt
#                        print(f"g_cnt is {g_cnt}")
#                        print(f"cnt is {cnt}")

                        if hantei == 0:
                            with open(os.path.join(DST_DIR, 'result.txt'), 'a') as f:
                                #                                print(line)
                                f.write(json.dumps(line) + '\n')
                        elif hantei == 1:
                            tmp += 1
#                            print("tobasitayo")
#                            print("--- --- --- --- --- --- --")
                            continue
                except Exception as e:
                    print('--- --- --- ---')
                    print(e)
        os.rename(os.path.join(SRC_DIR, file), os.path.join('/root/dst', file))

    with open(os.path.join(DST_DIR, 'preValue.txt'), 'w') as f:
        #        f.write(str(g_volt)+"\n")
        f.write(str(preValue)+"\n")
    with open(os.path.join(DST_DIR, 'cnt.txt'), 'w') as f:
        f.write(str(g_cnt)+"\n")

    filename = "taiwan_" + date_time + ".csv"

    if os.path.exists(os.path.join(DST_DIR, 'result.txt')):
        os.rename(os.path.join(DST_DIR, 'result.txt'),
                  os.path.join(DST_DIR, filename))
    else:
        print("result.txt is not exist")
    print(f"mabiitakazu is {tmp}")
