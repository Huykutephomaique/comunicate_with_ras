package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

type SystemData struct {
	Msg            string `json:"msg"`
	PowerGoodCount int    `json:"powerGoodCount"`
	PowerGoodTime  int    `json:"powerGoodTime"`
	Rtc            string `json:"rtc"`
	Type           string `json:"type"`
	UpTime         int    `json:"upTime"`
	Name           string `json:"name,omitempty"`
}

func convertRtcToTimestamp(rtc string) (int64, error) {
	t, err := time.Parse("20060102150405", rtc)
	if err != nil {
		return 0, err
	}
	return t.UnixMilli(), nil
}

func main() {
	filePath := "/root/src/system.json"
	deviceName := "APOSA1"

	// Đọc file
	file, err := os.Open(filePath)
	if err != nil {
		fmt.Printf("Error opening file: %v\n", err)
		return
	}
	defer file.Close()

	// Đọc và parse JSON
	var systemData SystemData
	if err := json.NewDecoder(file).Decode(&systemData); err != nil {
		fmt.Printf("Error parsing JSON: %v\n", err)
		return
	}

	// Thêm name vào systemData
	systemData.Name = deviceName

	// Tạo JSON mới với name
	modifiedJSON, err := json.Marshal(systemData)
	if err != nil {
		fmt.Printf("Error creating modified JSON: %v\n", err)
		return
	}

	// Tạo request
	req, err := http.NewRequest("POST", "http://47.107.233.129:10060/upload/", bytes.NewBuffer(modifiedJSON))
	if err != nil {
		fmt.Printf("Error creating request: %v\n", err)
		return
	}

	// Set headers
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer ABCDEFG")

	// Thêm timeout cho client
	client := &http.Client{
		Timeout: time.Second * 30,
	}

	// Gửi request
	resp, err := client.Do(req)
	if err != nil {
		fmt.Printf("Error sending request: %v\n", err)
		return
	}
	defer resp.Body.Close()

	// Đọc response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Printf("Error reading response: %v\n", err)
		return
	}

	fmt.Printf("Response status: %s\n", resp.Status)
	fmt.Printf("Response body: %s\n", string(body))
}
