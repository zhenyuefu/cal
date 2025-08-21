package main

import (
	"log"
	"net/http"
	"os"
	"cal"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	http.HandleFunc("/api/v2/cal", cal.Handler)
	http.HandleFunc("/api/v2/health", cal.Handler)
	
	// Serve static files for development
	http.Handle("/", http.FileServer(http.Dir("../../")))

	log.Printf("Go API server starting on port %s", port)
	log.Printf("Calendar API: http://localhost:%s/api/v2/cal", port)
	log.Printf("Health check: http://localhost:%s/api/v2/health", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}