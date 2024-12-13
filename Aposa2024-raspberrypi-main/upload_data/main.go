package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/joho/godotenv"
)

// Struct để parse dữ liệu sensor từ file
type SensorData struct {
	Name    string  `json:"name"`
	Volt    float64 `json:"volt"`
	Current float64 `json:"current"`
	Temp    float64 `json:"temp"`
	Rtc     string  `json:"rtc"` // Format: "20240311123456"
}

func dirwalk(dir string, target_name []string) []string {
	fmt.Printf("\n=== Starting dirwalk for directory: %s ===\n", dir)
	fmt.Printf("Looking for files with prefixes: %v\n", target_name)

	files, err := ioutil.ReadDir(dir)
	if err != nil {
		fmt.Printf("Error reading directory: %v\n", err)
		panic(err)
	}

	var paths2 []string
	for _, file := range files {
		if file.IsDir() {
			fmt.Printf("Found subdirectory: %s\n", file.Name())
			paths2 = append(paths2, dirwalk(filepath.Join(dir, file.Name()), target_name)...)
			continue
		}
		for _, tn := range target_name {
			if strings.HasPrefix(file.Name(), tn) {
				fullPath := filepath.Join(dir, file.Name())
				fmt.Printf("Found matching file: %s\n", fullPath)
				paths2 = append(paths2, fullPath)
			}
		}
	}

	fmt.Printf("=== Dirwalk completed. Found %d matching files ===\n", len(paths2))
	return paths2
}

func do_copy(sourceFile string, destinationFile string, src string) {
	fmt.Printf("\n=== Starting file copy ===\n")
	fmt.Printf("Source: %s\n", sourceFile)
	fmt.Printf("Destination: %s\n", destinationFile)

	input, err := ioutil.ReadFile(sourceFile)
	if err != nil {
		fmt.Printf("Error reading source file: %v\n", err)
		return
	}

	err = ioutil.WriteFile(destinationFile, input, 0644)
	if err != nil {
		fmt.Printf("Error creating destination file: %v\n", err)
		return
	}

	fmt.Printf("File copied successfully\n")
}

func Chunks(l []string, n int) chan []string {
	fmt.Printf("\n=== Creating chunks of size %d for %d items ===\n", n, len(l))

	ch := make(chan []string)
	go func() {
		for i := 0; i < len(l); i += n {
			from_idx := i
			to_idx := i + n
			if to_idx > len(l) {
				to_idx = len(l)
			}
			fmt.Printf("Sending chunk from index %d to %d\n", from_idx, to_idx)
			ch <- l[from_idx:to_idx]
		}
		close(ch)
	}()
	return ch
}

func convertRtcToTimestamp(rtc string) (int64, error) {
	fmt.Printf("\n=== Converting RTC to timestamp: %s ===\n", rtc)
	t, err := time.Parse("20060102150405", rtc)
	if err != nil {
		fmt.Printf("Error parsing RTC: %v\n", err)
		return 0, err
	}
	timestamp := t.UnixMilli()
	fmt.Printf("Converted to timestamp: %d\n", timestamp)
	return timestamp, nil
}

func write_file(paths []string, target_name string, url string) []string {
	fmt.Printf("\n=== Starting write_file ===\n")
	fmt.Printf("Processing %d paths\n", len(paths))
	fmt.Printf("Target name: %s\n", target_name)
	fmt.Printf("URL: %s\n", url)

	target_name2 := []string{"taiwan", "japan"}
	file_read, err := os.OpenFile(target_name, os.O_RDWR|os.O_CREATE|os.O_APPEND, 0666)
	if err != nil {
		fmt.Printf("Error opening target file: %v\n", err)
		fmt.Fprintf(os.Stderr, "fatal: error: %s", err.Error())
	}
	defer file_read.Close()

	lines := []string{}
	scanner := bufio.NewScanner(file_read)
	for scanner.Scan() {
		lines = append(lines, scanner.Text())
	}
	if serr := scanner.Err(); serr != nil {
		fmt.Printf("Scanner error: %v\n", serr)
		fmt.Fprintf(os.Stderr, "fatal: error: %s", err.Error())
	}

	fmt.Printf("Read %d existing lines from file\n", len(lines))

	set := make(map[string]bool)
	for _, v := range lines {
		set[v] = true
	}

	paths3 := []string{}
	for _, v := range paths {
		if set[v] != true {
			paths3 = append(paths3, v)
		}
	}

	fmt.Printf("Found %d new paths to process\n", len(paths3))

	size := 1000
	for l := range Chunks(paths3, size) {
		fmt.Printf("Processing chunk of %d files\n", len(l))
		for _, v := range l {
			for _, tn := range target_name2 {
				if strings.Contains(v, tn) == true {
					fmt.Printf("\nProcessing file: %s for target: %s\n", v, tn)
					ret, err := file_upload(v, tn, url)
					if err != nil {
						fmt.Printf("Upload error: %v\n", err)
					}
					if ret == 0 {
						fmt.Printf("File processed successfully, writing to log: %s\n", v)
						fmt.Fprintln(file_read, v)
						if err2 := os.Remove(v); err2 != nil {
							fmt.Printf("Error removing file: %v\n", err2)
						} else {
							fmt.Printf("File removed successfully: %s\n", v)
						}
					}
				}
			}
		}
		break
	}
	return paths3
}

var client = &http.Client{}

func file_upload(file_path string, target_name string, url string) (int, error) {
	fmt.Printf("\n=== Starting file upload ===\n")
	fmt.Printf("File path: %s\n", file_path)
	fmt.Printf("Target name: %s\n", target_name)
	fmt.Printf("URL: %s\n", url)

	token := "bBxXd3DuMl1lcW5OMixAbfbjL4azkHAposa1"
	var buf bytes.Buffer
	w := multipart.NewWriter(&buf)

	file, err := os.Open(file_path)
	if err != nil {
		fmt.Printf("Error opening file: %v\n", err)
		return 1, err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	if !scanner.Scan() {
		fmt.Printf("Error: empty file\n")
		return 1, fmt.Errorf("empty file")
	}

	firstLine := scanner.Text()
	fmt.Printf("First line content: %s\n", firstLine)

	var sensorData SensorData
	if err := json.Unmarshal([]byte(firstLine), &sensorData); err != nil {
		fmt.Printf("Error parsing JSON: %v\n", err)
		fmt.Printf("Problematic content: %s\n", firstLine)
		return 1, err
	}

	fmt.Printf("Successfully parsed sensor data: %+v\n", sensorData)

	timestamp, err := convertRtcToTimestamp(sensorData.Rtc)
	if err != nil {
		fmt.Printf("Error converting RTC: %v\n", err)
		return 1, err
	}

	if err := w.WriteField("timestamp", fmt.Sprintf("%d", timestamp)); err != nil {
		fmt.Printf("Error adding timestamp to form: %v\n", err)
		return 1, err
	}

	fw, err := w.CreateFormFile("file", filepath.Base(file_path))
	if err != nil {
		fmt.Printf("Error creating form file: %v\n", err)
		return 1, err
	}

	file.Seek(0, 0)
	if _, err = io.Copy(fw, file); err != nil {
		fmt.Printf("Error copying file content: %v\n", err)
		return 1, err
	}

	w.Close()

	req, err := http.NewRequest("POST", "http://47.107.233.129:10080/upload/", &buf)
	if err != nil {
		fmt.Printf("Error creating request: %v\n", err)
		return 1, err
	}

	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Content-Type", w.FormDataContentType())

	fmt.Printf("Request prepared:\n")
	fmt.Printf("URL: http://47.107.233.129:10080/upload/\n")
	fmt.Printf("Headers: Authorization: Bearer %s..., Content-Type: %s\n",
		token[:10], w.FormDataContentType())

	client := &http.Client{
		Timeout: time.Second * 30,
	}

	fmt.Printf("Sending request...\n")
	resp, err := client.Do(req)
	if err != nil {
		fmt.Printf("Request failed: %v\n", err)
		return 1, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Printf("Error reading response: %v\n", err)
		return 1, err
	}

	fmt.Printf("Response status: %s\n", resp.Status)
	fmt.Printf("Response body: %s\n", string(body))
	fmt.Printf("Upload completed successfully\n")

	return 0, nil
}

func main() {
	fmt.Println("\n=== Application Starting ===\n")

	err := godotenv.Load()
	if err != nil {
		fmt.Printf("Error loading .env file: %v\n", err)
		os.Exit(1)
	}

	source_dirname := os.Getenv("SOURCE_DIRNAME")
	dest_dirname := os.Getenv("DEST_DIRNAME")
	upload_url := os.Getenv("TARGET_URL")

	fmt.Printf("Configuration loaded:\n")
	fmt.Printf("Source directory: %s\n", source_dirname)
	fmt.Printf("Destination directory: %s\n", dest_dirname)
	fmt.Printf("Upload URL: %s\n", upload_url)

	target_name := []string{"taiwan", "japan"}
	copy_list := source_dirname + "\\copy_list.txt"

	fmt.Printf("Copy list path: %s\n", copy_list)

	for {
		fmt.Printf("\n=== Starting new processing cycle ===\n")

		file_read, err := os.OpenFile(copy_list, os.O_RDWR|os.O_CREATE|os.O_APPEND, 0666)
		if err != nil {
			fmt.Printf("Error opening copy list: %v\n", err)
			continue
		}

		lines := []string{}
		scanner := bufio.NewScanner(file_read)
		for scanner.Scan() {
			lines = append(lines, scanner.Text())
		}
		if err := scanner.Err(); err != nil {
			fmt.Printf("Error scanning copy list: %v\n", err)
			file_read.Close()
			continue
		}

		fmt.Printf("Read %d lines from copy list\n", len(lines))

		set := make(map[string]bool)
		for _, v := range lines {
			set[v] = true
		}

		upload_files := dirwalk(source_dirname, target_name)
		fmt.Printf("Found %d files to process\n", len(upload_files))

		paths3 := []string{}
		for _, v := range upload_files {
			if !set[v] {
				paths3 = append(paths3, v)
			}
		}

		fmt.Printf("Found %d new files to process\n", len(paths3))

		for _, file := range paths3 {
			fmt.Printf("Copying file: %s\n", file)
			fmt.Fprintln(file_read, file)
			do_copy(file, filepath.Join(dest_dirname, filepath.Base(file)), file)
		}

		write_file(upload_files, filepath.Join(source_dirname, "2021v1_DataLogger_list.txt"), upload_url)
		file_read.Close()

		fmt.Printf("=== Cycle completed, sleeping for 5 seconds ===\n\n")
		time.Sleep(time.Second * 5)
	}
}
