package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"io"
)

// Import the handler from the cal package
import "cal"

func main() {
	// Create a test request with some query parameters
	req := httptest.NewRequest("GET", "/?MAJ=DAC&LRC=2&MLBDA=1", nil)
	w := httptest.NewRecorder()
	
	// Call the handler
	cal.Handler(w, req)
	
	// Print the response
	resp := w.Result()
	body, _ := io.ReadAll(resp.Body)
	
	fmt.Printf("Status: %d\n", resp.StatusCode)
	fmt.Printf("Content-Type: %s\n", resp.Header.Get("Content-Type"))
	fmt.Printf("Body length: %d\n", len(body))
	
	// Print first few lines of the body to see if it's valid ICS
	lines := strings.Split(string(body), "\r\n")
	fmt.Println("First 10 lines:")
	for i, line := range lines {
		if i >= 10 {
			break
		}
		fmt.Printf("%d: %s\n", i+1, line)
	}
}