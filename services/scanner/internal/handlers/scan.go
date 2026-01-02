// Package handlers - Scan request handlers
package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"

	"github.com/autodoc/scanner/internal/scanner"
)

// ScanRequest represents a repository scan request
type ScanRequest struct {
	URL    string `json:"url" binding:"required"`
	Branch string `json:"branch"`
	Token  string `json:"token"`
}

// ScanRepository handles repository scan requests
func ScanRepository(c *gin.Context) {
	var req ScanRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "URL is required"})
		return
	}

	// Generate scan ID
	scanID := uuid.New().String()

	// Start scan in background goroutine
	go func() {
		scanner.StartScan(scanID, req.URL, req.Branch, req.Token)
	}()

	c.JSON(http.StatusAccepted, gin.H{
		"scan_id": scanID,
		"status":  "queued",
		"message": "Scan started, check status at /scan/" + scanID,
	})
}

// GetScanStatus returns the status of a scan
func GetScanStatus(c *gin.Context) {
	scanID := c.Param("id")

	status, err := scanner.GetStatus(scanID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Scan not found"})
		return
	}

	c.JSON(http.StatusOK, status)
}

// GetEndpoints returns the detected endpoints from a scan
func GetEndpoints(c *gin.Context) {
	scanID := c.Param("id")

	endpoints, err := scanner.GetEndpoints(scanID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Scan not found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"scan_id":   scanID,
		"count":     len(endpoints),
		"endpoints": endpoints,
	})
}
