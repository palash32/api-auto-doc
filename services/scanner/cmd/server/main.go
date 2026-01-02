// Package main - API Discovery Engine
// High-performance repository scanner written in Go
package main

import (
	"log"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"

	"github.com/autodoc/scanner/internal/handlers"
	"github.com/autodoc/scanner/internal/scanner"
)

func main() {
	// Load environment variables
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found, using environment variables")
	}

	// Get port from environment
	port := os.Getenv("PORT")
	if port == "" {
		port = "3001"
	}

	// Set Gin mode
	if os.Getenv("GIN_MODE") == "release" {
		gin.SetMode(gin.ReleaseMode)
	}

	// Initialize scanner
	scanner.Initialize()

	// Create router
	r := gin.Default()

	// Health check
	r.GET("/health", handlers.HealthCheck)
	r.GET("/health/ready", handlers.ReadyCheck)
	r.GET("/health/live", handlers.LiveCheck)

	// Scan endpoints
	r.POST("/scan", handlers.ScanRepository)
	r.GET("/scan/:id", handlers.GetScanStatus)
	r.GET("/scan/:id/endpoints", handlers.GetEndpoints)

	// Start server
	log.Printf(`
╔═══════════════════════════════════════════════════════════╗
║         API Discovery Engine - Go Scanner                  ║
╠═══════════════════════════════════════════════════════════╣
║  🚀 Server:     http://localhost:%s                       ║
║  🔧 Environment: %s                                       ║
╚═══════════════════════════════════════════════════════════╝
`, port, os.Getenv("GIN_MODE"))

	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
