// Package handlers - HTTP request handlers
package handlers

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

var startTime = time.Now()

// HealthCheck returns the health status of the service
func HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":    "healthy",
		"version":   "2.0.0",
		"service":   "scanner",
		"timestamp": time.Now().Format(time.RFC3339),
		"uptime":    time.Since(startTime).String(),
	})
}

// ReadyCheck returns whether the service is ready to accept requests
func ReadyCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"ready": true,
	})
}

// LiveCheck returns whether the service is alive
func LiveCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"live": true,
	})
}
