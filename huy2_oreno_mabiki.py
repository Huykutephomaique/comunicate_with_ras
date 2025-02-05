import os
import json
import pdb
import datetime
import sys
import serial
import time
import subprocess
import signal

def run_go_program(go_executable, timeout=5):
    """
    Chạy chương trình Go đã build và dừng nó sau một khoảng thời gian.

    Args:
        go_executable (str): Đường dẫn đến file Go đã build.
        timeout (int): Thời gian chạy trước khi dừng (giây).

    Returns:
        bool: True nếu dừng thành công, False nếu có lỗi.
    """
    try:
        # Chạy chương trình Go (không chờ kết quả)
        process = subprocess.Popen([go_executable], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print(f"Chương trình Go đang chạy với PID: {process.pid}")

        # Chờ trong khoảng thời gian quy định
        time.sleep(timeout)

        # Kiểm tra xem tiến trình còn chạy không
        if process.poll() is None:
            print("Dừng chương trình Go...")
            process.terminate()  # Gửi tín hiệu SIGTERM để dừng
            time.sleep(1)  # Đợi 1 giây để tiến trình dừng hẳn

            # Nếu tiến trình vẫn còn chạy, dùng SIGKILL
            if process.poll() is None:
                os.kill(process.pid, signal.SIGKILL)
                print("Đã buộc dừng chương trình Go bằng SIGKILL.")

        print("Chương trình Go đã được dừng.")
        return True

    except Exception as e:
        print(f"Lỗi khi chạy chương trình Go: {e}")
        return False
    
def update_json_key(file_path, key ,value):
    """
    Đọc file JSON, cập nhật giá trị của một khóa, và ghi lại file.

    Args:
        file_path (str): Đường dẫn tới file JSON.
        key (str): Khóa cần cập nhật giá trị.
        value (any): Giá trị mới cho khóa.

    Returns:
        bool: True nếu cập nhật thành công, False nếu xảy ra lỗi.
    """
    rewrite_path = 'root/src/stk23_system.json'
    key = 'powerGoodCount'
    try:
        # Đọc file JSON
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Cập nhật giá trị cho khóa
        if key in data:
            data[key] = value
        else:
            print(f"Key '{key}' không tồn tại trong file JSON.")
            return False

        # Ghi lại file JSON
        with open(rewrite_path, 'w') as file:
            json.dump(data, file, indent=4)#indent = none
        return True

    except Exception as e:
        print(f"Lỗi: {e}")
        return False

def getPowercount():
    with open('root/src2/powercount.txt') as f:
        line = f.read().strip()
    try:
        return int(line)
    except:
        return 0
    
def getPrevious():
    with open('root/src2/preValue.txt') as f:
        line = f.read().strip()
    try:
        return int(line)
    except:
        return 0

def getCount():
    with open('root/src2/cnt.txt') as f:
        line = f.read().strip()
    try:
        return int(line)
    except:
        return 0

def writeCount():
    file_path = "root/src2/cnt.txt"
    try:
        with open(file_path, 'w') as file:
            file.write('0')
        print(f"{file_path}の内容を0に設定しました。")
    except Exception as e:
        print(f"ファイルの書き込みに失敗しました: {e}")

def getHantei(preValue,volt,cnt,powercount,rtc_huy):
#    pdb.set_trace()
#    print(f"cnt is {cnt}")
#    print(f"preValue is {preValue}")
#    print(f"volt is {volt}")
    go_executable = "/root/Aposa2024-raspberrypi/power_count/main"

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

    if (int(preValue) - int(volt) >10): #(int(preValue) - int(volt) >10):
        powercount += 1
        print(f'ghi power count neeeeeeeeeee{powercount}')
        update_json_key(powercount_path,'powerGoodCount',powercount)
        update_json_key(powercount_path,'rtc',rtc_huy)
        run_go_program(go_executable, timeout=3)
        with open('root/src2/powercount.txt','w') as f:
            f.write(str(powercount)+"\n")    

    if cnt <= 1000 and volt > 15:
        return 0,volt,cnt,powercount
    elif cnt <= 1000 and volt < 2:
#    elif cnt <= 45000 and volt < 2:
        return 0,volt,cnt,powercount

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
    
        data=json.dumps(data)
        a = data + "\n"

#2024_07_03 writeCount()実装
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

        return 1,volt,cnt,powercount
#        return 0,volt,cnt,powercount
#2024_07_18 ソレノイドオフから10s以降は間引きデータを描画
    elif cnt > 1000 and volt < 2:
        if cnt % 100 == 0:
            return 0,volt,cnt,powercount
        else:
            return 1,volt,cnt,powercount
    elif cnt > 1000 and volt > 15:
        if cnt % 100 == 0:
            return 0,volt,cnt,powercount
        else:
            return 1,volt,cnt,powercount
    else:
        print('----------')
        print("kore detya dame dayo?")
        return 0,volt,cnt,powercount
        sys.exit()

if __name__ == '__main__':
    now = datetime.datetime.now()
    date_time = now.strftime("%Y_%m_%d_%H_%M_%S")
    powercount_path = 'root/src/system.json'
    SRC_DIR = 'root/src'
    DST_DIR = 'root/src2'
    PREFIX = 'taiwan_'
    # init
    if not os.path.exists(os.path.join(DST_DIR,'powercount.txt')):
        print("path not exit")
        with open(os.path.join(DST_DIR,'powercount.txt'),'w') as f:
            f.write("0\n")

    if not os.path.exists(os.path.join(DST_DIR,'preValue.txt')):
        print("koreha saisyono ikkaidake") #pass not exist
        with open(os.path.join(DST_DIR,'preValue.txt'),'w') as f:
            #f.write("24\n")
            f.write("0\n")
    if not os.path.exists(os.path.join(DST_DIR,'cnt.txt')):
        print("koreha saisyono ikkaidake")
        with open(os.path.join(DST_DIR,'cnt.txt'),'w') as f:
            f.write("0\n")

#    pdb.set_trace()

    # gaibu kara preValue kaisyuu 
    powercount = getPowercount()
    print(powercount)
    update_json_key(powercount_path,'powerGoodCount',powercount)

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
        with open(os.path.join(SRC_DIR,file)) as f:
            lines = f.readlines()

        for  line in lines:
            if line != '\n':
                line = line.replace("'",'"')
                try:
                    line = json.loads(line)
                    volt = line.get('volt')
                    g_volt = line.get('volt')
                    rtc_huy = line.get('rtc')

                    if volt is not None:
                        if volt > 15000:
                            volt = 24
                            g_volt = 24
                        else:
                            volt = 0
                            g_volt = 0
#                        hantei,volt,cnt = getHantei(preValue,volt,cnt)
                        hantei,volt,cnt,powercount = getHantei(preValue,g_volt,g_cnt,powercount,rtc_huy)
                        preValue = volt
                        g_cnt = cnt
#                        print(f"g_cnt is {g_cnt}")
#                        print(f"cnt is {cnt}")
        
                        if hantei == 0:
                            with open(os.path.join(DST_DIR,'result.txt'),'a') as f:
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
        os.rename(os.path.join(SRC_DIR,file),os.path.join('root/dst',file))


    with open(os.path.join(DST_DIR,'preValue.txt'),'w') as f:
#        f.write(str(g_volt)+"\n")
        f.write(str(preValue)+"\n")
    with open(os.path.join(DST_DIR,'cnt.txt'),'w') as f:
        f.write(str(g_cnt)+"\n")

    filename = "taiwan_" + date_time + ".csv"

    if os.path.exists(os.path.join(DST_DIR,'result.txt')):
        os.rename(os.path.join(DST_DIR,'result.txt'),os.path.join(DST_DIR,filename))
    else:
        print("result.txt is not exist")
    print(f"mabiitakazu is {tmp}")
