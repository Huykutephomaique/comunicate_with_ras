import os
import json
import pdb
import datetime
import sys
import serial
import time
import subprocess
import signal
import threading

GO_EXECUTABLE = "root/Aposa2024-raspberrypi/power_count/main"
MAX_RETRIES = 3  # Số lần thử lại tối đa
TIMEOUT = 0.05  # Giới hạn thời gian chạy (50ms)

def run_go_program(go_executable, timeout=TIMEOUT, retries=MAX_RETRIES):
    """
    Chạy chương trình Go và tự động thử lại nếu thất bại.
    Giới hạn thời gian tối đa để tránh bị treo lâu.
    """
    for attempt in range(1, retries + 1):
        try:
            start_time = time.time()
            process = subprocess.Popen([go_executable], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[Lần {attempt}] Chương trình Go chạy với PID: {process.pid}")

            # Tạo một luồng riêng để dừng sau `timeout` giây
            stop_process_after_timeout(process, timeout)

            # Chờ tiến trình kết thúc trong thời gian tối đa
            try:
                process.wait(timeout)
            except subprocess.TimeoutExpired:
                print(f"[Lần {attempt}] Quá thời gian {timeout * 1000:.0f}ms, thử lại...")
                continue  # Chạy lại vòng lặp

            # Nếu tiến trình kết thúc sớm hơn timeout, tính thời gian thực tế
            elapsed_time = (time.time() - start_time) * 1000  # Đổi sang ms
            print(f"[Lần {attempt}] Gửi thành công trong {elapsed_time:.2f}ms")
            return  # Thành công, không cần thử lại nữa

        except Exception as e:
            print(f"[Lần {attempt}] Lỗi: {e}")

    print("❌ Đã thử 3 lần nhưng vẫn thất bại!")
    
def stop_process_after_timeout(process, timeout):
    """Tạo một luồng riêng để dừng tiến trình sau `timeout` giây mà không chặn chương trình chính"""
    def stop():
        if process.poll() is None:  # Nếu tiến trình vẫn đang chạy
            print("Dừng chương trình Go...")
            process.terminate()
            threading.Timer(0.01, lambda: os.kill(process.pid, signal.SIGKILL) if process.poll() is None else None).start()
    
    threading.Timer(timeout, stop).start()
    
def update_json_key(file_path, key , value, pc):
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
    key_pc = 'powerGoodCount'
    try:
        # Đọc file JSON
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Cập nhật giá trị cho khóa
        if key in data:
            data[key] = value
            print(f"da cap nha '{key}-------{value}' ")
        else:
            print(f"Key '{key}' không tồn tại trong file JSON.")
        # Cập nhật giá trị cho khóa
        if key_pc in data:
            data[key_pc] = pc
            print(f"da cap nha '{key}-------{pc}' ")
        else:
            print(f"Key '{key}' không tồn tại trong file JSON.")
        # Ghi lại file JSON
        with open(rewrite_path, 'w') as file:
            json.dump(data, file, indent=4)#indent = none
        
    except Exception as e:
        print(f"Lỗi: {e}")

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
    powercount_path = 'root/src/system.json'
    if int(preValue) == int(volt):
#        print(f"-------------------------------------------{powercount}-")
        cnt += 1
    else:
        print("--------------------------------------------")
        print("koko derutoki aruno?")
        print(f"preValuje is {preValue}")
        print(f"preCnt is {cnt}")
        print(f"now volt is {volt}") 
        print("--------------------------------------------")
        cnt = 0

    if ( int(preValue) - int(volt) >10 ): #(int(preValue) - int(volt) >10):
        powercount += 1
        print(f'ghi power count neeeeeeeeeee{powercount}')
        update_json_key(powercount_path,'rtc',rtc_huy,powercount)
        run_go_program(GO_EXECUTABLE, timeout=TIMEOUT, retries=MAX_RETRIES)
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
    print(f"get powercount ---- {powercount}")
    update_json_key(powercount_path,'powerGoodCount',powercount,powercount)

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

    first = 1
    for file in files:
        with open(os.path.join(SRC_DIR,file)) as f:
            lines = f.readlines()
            fake_lines = lines
        if first == 1: 
            for i in fake_lines[:4]:
                if i != '\n':
                    i = i.replace("'",'"')
                    try:
                        i = json.loads(i)
                        volt = i.get('volt')
                        rtc_huy = i.get('rtc')

                        if volt is not None:
                            #cập nhật rtc: 
                            update_json_key(powercount_path,'rtc',rtc_huy,powercount)
                            run_go_program(GO_EXECUTABLE, timeout=TIMEOUT, retries=MAX_RETRIES) 

                    except Exception as e:
                        print('--- --- --- ---')
        
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
        first += 1


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