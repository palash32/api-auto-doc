// Package scanner - Core scanning functionality
package scanner

import (
	"bufio"
	"fmt"
	"io/fs"
	"log"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"time"

	"github.com/go-git/go-git/v5"
	"github.com/go-git/go-git/v5/plumbing"
	"github.com/go-git/go-git/v5/plumbing/transport/http"
)

// Configuration constants
const (
	MaxFileSize    = 1024 * 1024 // 1MB
	MaxFilesToScan = 1000
	CloneTimeout   = 5 * time.Minute
)

// Endpoint represents a detected API endpoint
type Endpoint struct {
	ID          string   `json:"id"`
	Path        string   `json:"path"`
	Method      string   `json:"method"`
	Summary     string   `json:"summary"`
	Description string   `json:"description"`
	Tags        []string `json:"tags"`
	FilePath    string   `json:"file_path"`
	LineNumber  int      `json:"line_number"`
}

// ScanStatus represents the status of a scan
type ScanStatus struct {
	ID           string     `json:"id"`
	Status       string     `json:"status"` // queued, scanning, completed, failed
	URL          string     `json:"url"`
	FilesScanned int        `json:"files_scanned"`
	Endpoints    int        `json:"endpoint_count"`
	StartedAt    time.Time  `json:"started_at"`
	CompletedAt  *time.Time `json:"completed_at,omitempty"`
	Error        string     `json:"error,omitempty"`
}

var (
	scans     = make(map[string]*ScanStatus)
	endpoints = make(map[string][]Endpoint)
	mu        sync.RWMutex
)

// API Indicator patterns for Stage 1 (Pre-filtering)
var (
	pythonIndicators = []*regexp.Regexp{
		regexp.MustCompile(`@\w+\.(get|post|put|patch|delete|options|head)`),
		regexp.MustCompile(`@\w+\.route`),
		regexp.MustCompile(`\b(path|re_path)\s*\(`),
		regexp.MustCompile(`\b(APIRouter|Blueprint)\b`),
		regexp.MustCompile(`from\s+fastapi\s+import`),
		regexp.MustCompile(`from\s+flask\s+import`),
	}

	jsIndicators = []*regexp.Regexp{
		regexp.MustCompile(`\.(get|post|put|patch|delete|options|head|all)\s*\(`),
		regexp.MustCompile(`@(Get|Post|Put|Patch|Delete|Options|Head|Controller)\b`),
		regexp.MustCompile(`\b(Router|express|fastify)\s*\(`),
		regexp.MustCompile(`from\s+['"](@nestjs|express|fastify)`),
		regexp.MustCompile(`import.*\{.*Router.*\}`),
	}

	goIndicators = []*regexp.Regexp{
		regexp.MustCompile(`\.(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s*\(`),
		regexp.MustCompile(`\bHandleFunc\s*\(`),
		regexp.MustCompile(`\bServeHTTP\b`),
		regexp.MustCompile(`"github\.com/(gin-gonic|labstack|gofiber)`),
	}

	javaIndicators = []*regexp.Regexp{
		regexp.MustCompile(`@(GetMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping|RequestMapping)`),
		regexp.MustCompile(`@RestController`),
		regexp.MustCompile(`@Controller`),
	}

	csharpIndicators = []*regexp.Regexp{
		regexp.MustCompile(`\[(HttpGet|HttpPost|HttpPut|HttpPatch|HttpDelete)\]`),
		regexp.MustCompile(`\[Route\(`),
		regexp.MustCompile(`\[ApiController\]`),
	}
)

// Endpoint extraction patterns for Stage 2 (Deep extraction)
var (
	// Python patterns
	pythonPatterns = []*regexp.Regexp{
		// FastAPI - flexible variable names
		regexp.MustCompile(`@\w+\.(get|post|put|patch|delete|options|head)\s*\(\s*["']([^"']+)["']`),
		// Flask - route with methods
		regexp.MustCompile(`@\w+\.route\s*\(\s*["']([^"']+)["'].*?methods\s*=\s*\[["']([^"'\]]+)["']`),
		// Flask - simple route (defaults to GET)
		regexp.MustCompile(`@\w+\.route\s*\(\s*["']([^"']+)["']`),
		// Django URL patterns
		regexp.MustCompile(`(?:path|re_path)\s*\(\s*["']([^"']+)["']`),
	}

	// JavaScript/TypeScript patterns
	jsPatterns = []*regexp.Regexp{
		// Express/Fastify - any variable name
		regexp.MustCompile(`\w+\.(get|post|put|patch|delete|options|head|all)\s*\(\s*["'\x60]([^"'\x60]+)["'\x60]`),
		// NestJS decorators
		regexp.MustCompile(`@(Get|Post|Put|Patch|Delete|Options|Head)\s*\(\s*["']?([^"'\)]*?)["']?\s*\)`),
	}

	// Go patterns
	goPatterns = []*regexp.Regexp{
		// Gin, Echo - method-specific
		regexp.MustCompile(`\w+\.(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s*\(\s*["']([^"']+)["']`),
		// Standard library
		regexp.MustCompile(`HandleFunc\s*\(\s*["']([^"']+)["']`),
		// Gorilla mux
		regexp.MustCompile(`Handle(?:Func)?\s*\(\s*["']([^"']+)["'].*?\.Methods\s*\(\s*["']([^"']+)["']`),
	}

	// Java patterns
	javaPatterns = []*regexp.Regexp{
		// Spring Boot method-level mappings
		regexp.MustCompile(`@(GetMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping)\s*\(\s*(?:value\s*=\s*)?["']([^"'\)]+)["']`),
		// Note: @RequestMapping is typically used at class level, not extracted as endpoint
	}

	// C# patterns
	csharpPatterns = []*regexp.Regexp{
		// ASP.NET Web API
		regexp.MustCompile(`\[(HttpGet|HttpPost|HttpPut|HttpPatch|HttpDelete)\s*\(\s*"([^"]+)"\s*\)\]`),
		regexp.MustCompile(`\[Route\s*\(\s*"([^"]+)"\s*\)\]`),
	}
)

// Directories to skip during scanning
var excludedDirs = map[string]bool{
	"node_modules": true,
	".git":         true,
	"vendor":       true,
	"__pycache__":  true,
	"venv":         true,
	".venv":        true,
	"env":          true,
	".env":         true,
	"dist":         true,
	"build":        true,
	"target":       true,
	".idea":        true,
	".vscode":      true,
	"bin":          true,
	"obj":          true,
}

// Supported file extensions
var supportedExtensions = map[string]bool{
	".py":   true,
	".js":   true,
	".ts":   true,
	".jsx":  true,
	".tsx":  true,
	".go":   true,
	".java": true,
	".cs":   true,
}

// Initialize sets up the scanner
func Initialize() {
	log.Println("🔍 Scanner initialized with enhanced patterns:")
	log.Printf("   Python indicators: %d patterns", len(pythonIndicators))
	log.Printf("   JavaScript/TypeScript indicators: %d patterns", len(jsIndicators))
	log.Printf("   Go indicators: %d patterns", len(goIndicators))
	log.Printf("   Java indicators: %d patterns", len(javaIndicators))
	log.Printf("   C# indicators: %d patterns", len(csharpIndicators))
}

// GetStatus returns the status of a scan
func GetStatus(scanID string) (*ScanStatus, error) {
	mu.RLock()
	defer mu.RUnlock()

	status, exists := scans[scanID]
	if !exists {
		return nil, fmt.Errorf("scan not found")
	}
	return status, nil
}

// GetEndpoints returns the detected endpoints for a scan
func GetEndpoints(scanID string) ([]Endpoint, error) {
	mu.RLock()
	defer mu.RUnlock()

	eps, exists := endpoints[scanID]
	if !exists {
		return nil, fmt.Errorf("scan not found")
	}
	return eps, nil
}

// cloneRepository clones a Git repository to a temporary directory
func cloneRepository(url, branch, token string) (string, error) {
	// Create temp directory
	tmpDir, err := os.MkdirTemp("", "scanner-*")
	if err != nil {
		return "", fmt.Errorf("failed to create temp dir: %w", err)
	}

	// Prepare clone options
	cloneOptions := &git.CloneOptions{
		URL:      url,
		Progress: nil, // Silent clone
	}

	// Add branch if specified
	if branch != "" {
		cloneOptions.ReferenceName = plumbing.NewBranchReferenceName(branch)
	}

	// Add authentication if token provided
	if token != "" {
		cloneOptions.Auth = &http.BasicAuth{
			Username: "x-access-token", // GitHub token auth
			Password: token,
		}
	}

	// Clone the repository
	log.Printf("📦 Cloning repository: %s", url)
	_, err = git.PlainClone(tmpDir, false, cloneOptions)
	if err != nil {
		os.RemoveAll(tmpDir) // Cleanup on error
		return "", fmt.Errorf("failed to clone repository: %w", err)
	}

	return tmpDir, nil
}

// hasAPIIndicators performs Stage 1 pre-filtering
func hasAPIIndicators(filePath, content string) bool {
	ext := strings.ToLower(filepath.Ext(filePath))

	var indicators []*regexp.Regexp
	switch ext {
	case ".py":
		indicators = pythonIndicators
	case ".js", ".ts", ".jsx", ".tsx":
		indicators = jsIndicators
	case ".go":
		indicators = goIndicators
	case ".java":
		indicators = javaIndicators
	case ".cs":
		indicators = csharpIndicators
	default:
		return false
	}

	// Quick scan for any indicator
	for _, pattern := range indicators {
		if pattern.MatchString(content) {
			return true
		}
	}

	return false
}

// getCodeFiles recursively finds all code files in a directory
func getCodeFiles(rootDir string) ([]string, error) {
	var files []string

	err := filepath.WalkDir(rootDir, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		// Skip excluded directories
		if d.IsDir() {
			if excludedDirs[d.Name()] {
				return filepath.SkipDir
			}
			return nil
		}

		// Check if file has supported extension
		ext := strings.ToLower(filepath.Ext(path))
		if supportedExtensions[ext] {
			files = append(files, path)
		}

		// Safety limit
		if len(files) >= MaxFilesToScan {
			return fmt.Errorf("max files limit reached")
		}

		return nil
	})

	return files, err
}

// getLikelyAPIFiles performs Stage 1 filtering
func getLikelyAPIFiles(rootDir string) ([]string, error) {
	allFiles, err := getCodeFiles(rootDir)
	if err != nil {
		return nil, err
	}

	var apiFiles []string
	totalFiles := len(allFiles)

	log.Printf("🔍 Pre-filtering %d code files for API indicators...", totalFiles)

	for _, filePath := range allFiles {
		// Check file size
		info, err := os.Stat(filePath)
		if err != nil {
			continue
		}
		if info.Size() > MaxFileSize {
			log.Printf("⚠️  Skipping large file: %s (%d bytes)", filePath, info.Size())
			continue
		}

		// Read file content
		content, err := os.ReadFile(filePath)
		if err != nil {
			continue
		}

		// Stage 1: Check for API indicators
		if hasAPIIndicators(filePath, string(content)) {
			apiFiles = append(apiFiles, filePath)
		}
	}

	passRate := float64(len(apiFiles)) / float64(totalFiles) * 100
	log.Printf("✅ Pre-filter complete: %d/%d files (%.1f%%) have API indicators",
		len(apiFiles), totalFiles, passRate)

	return apiFiles, nil
}

// StartScan begins scanning a repository
func StartScan(scanID, url, branch, token string) {
	// Initialize scan status
	mu.Lock()
	scans[scanID] = &ScanStatus{
		ID:        scanID,
		Status:    "scanning",
		URL:       url,
		StartedAt: time.Now(),
	}
	endpoints[scanID] = []Endpoint{}
	mu.Unlock()

	log.Printf("\n" + strings.Repeat("=", 70))
	log.Printf("🔍 SCAN STARTED: %s", scanID)
	log.Printf("📦 Repository: %s", url)
	if branch != "" {
		log.Printf("🌿 Branch: %s", branch)
	}
	log.Printf(strings.Repeat("=", 70))

	// Step 1: Clone repository
	log.Printf("\n📥 STEP 1/4: Cloning repository...")
	tmpDir, err := cloneRepository(url, branch, token)
	if err != nil {
		mu.Lock()
		now := time.Now()
		scans[scanID].Status = "failed"
		scans[scanID].Error = fmt.Sprintf("Failed to clone repository: %v", err)
		scans[scanID].CompletedAt = &now
		mu.Unlock()
		log.Printf("❌ FAILED: Unable to clone repository - %v", err)
		return
	}
	defer os.RemoveAll(tmpDir) // Cleanup temp directory
	log.Printf("✅ Repository cloned to: %s", tmpDir)

	// Step 2: Discover all code files
	log.Printf("\n📂 STEP 2/4: Discovering code files...")
	allFiles, err := getCodeFiles(tmpDir)
	if err != nil {
		mu.Lock()
		now := time.Now()
		scans[scanID].Status = "failed"
		scans[scanID].Error = fmt.Sprintf("Failed to discover files: %v", err)
		scans[scanID].CompletedAt = &now
		mu.Unlock()
		log.Printf("❌ FAILED: Unable to discover files - %v", err)
		return
	}
	log.Printf("📊 Found %d code files across supported languages", len(allFiles))

	// Step 3: Pre-filter for API files (Stage 1)
	log.Printf("\n🔍 STEP 3/4: Pre-filtering for API indicators...")
	log.Printf("   Scanning files for API framework markers...")

	apiFiles, err := getLikelyAPIFiles(tmpDir)
	if err != nil {
		mu.Lock()
		now := time.Now()
		scans[scanID].Status = "failed"
		scans[scanID].Error = fmt.Sprintf("Failed to scan files: %v", err)
		scans[scanID].CompletedAt = &now
		mu.Unlock()
		log.Printf("❌ FAILED: Pre-filtering error - %v", err)
		return
	}

	if len(apiFiles) == 0 {
		log.Printf("⚠️  No API files detected in repository")
		log.Printf("   This repository may not contain API endpoints")
	}

	// Step 4: Extract endpoints from API files (Stage 2)
	log.Printf("\n🎯 STEP 4/4: Extracting endpoints from API files...")
	var allEndpoints []Endpoint
	processedFiles := 0

	for _, filePath := range apiFiles {
		content, err := os.ReadFile(filePath)
		if err != nil {
			continue
		}

		// Extract relative path from repo root
		relPath, _ := filepath.Rel(tmpDir, filePath)

		// Scan file for endpoints
		fileEndpoints := ScanFile(relPath, string(content))
		if len(fileEndpoints) > 0 {
			allEndpoints = append(allEndpoints, fileEndpoints...)
			processedFiles++
			log.Printf("   📄 %s → %d endpoint(s)", relPath, len(fileEndpoints))
		}
	}

	// Final summary
	log.Printf("\n" + strings.Repeat("=", 70))
	log.Printf("✅ SCAN COMPLETED: %s", scanID)
	log.Printf("📊 Summary:")
	log.Printf("   • Total code files found: %d", len(allFiles))
	log.Printf("   • Files with API indicators: %d (%.1f%%)", len(apiFiles), float64(len(apiFiles))/float64(len(allFiles))*100)
	log.Printf("   • Files processed: %d", processedFiles)
	log.Printf("   • Endpoints discovered: %d", len(allEndpoints))
	log.Printf("   • Duration: %v", time.Since(scans[scanID].StartedAt).Round(time.Millisecond))
	log.Printf(strings.Repeat("=", 70) + "\n")

	// Update final status
	mu.Lock()
	now := time.Now()
	scans[scanID].Status = "completed"
	scans[scanID].FilesScanned = len(apiFiles)
	scans[scanID].Endpoints = len(allEndpoints)
	scans[scanID].CompletedAt = &now
	endpoints[scanID] = allEndpoints
	mu.Unlock()
}

// ScanFile scans a single file for API endpoints (Stage 2 - Deep extraction)
func ScanFile(filePath string, content string) []Endpoint {
	var found []Endpoint
	ext := strings.ToLower(filepath.Ext(filePath))

	var patterns []*regexp.Regexp
	switch ext {
	case ".py":
		patterns = pythonPatterns
	case ".js", ".ts", ".jsx", ".tsx":
		patterns = jsPatterns
	case ".go":
		patterns = goPatterns
	case ".java":
		patterns = javaPatterns
	case ".cs":
		patterns = csharpPatterns
	default:
		return found
	}

	scanner := bufio.NewScanner(strings.NewReader(content))
	lineNum := 0

	for scanner.Scan() {
		lineNum++
		line := scanner.Text()

		for _, pattern := range patterns {
			matches := pattern.FindStringSubmatch(line)
			if len(matches) >= 2 {
				var method, path string

				// Handle different pattern formats per language
				if ext == ".java" {
					// Java Spring Boot: @GetMapping, @PostMapping, etc.
					if len(matches) >= 3 {
						// Extract method from annotation (GetMapping -> GET)
						annotation := matches[1]
						if strings.HasSuffix(annotation, "Mapping") {
							method = strings.ToUpper(strings.TrimSuffix(annotation, "Mapping"))
						} else {
							method = strings.ToUpper(annotation)
						}
						path = matches[2]
					} else if len(matches) == 2 {
						// @RequestMapping with just path
						method = "GET" // Default
						path = matches[1]
					}
				} else if ext == ".py" {
					// Python - check which pattern matched
					if strings.Contains(line, ".route") && strings.Contains(line, "methods") && len(matches) == 3 {
						// Flask with methods: @bp.route('/path', methods=['GET'])
						// Pattern captures: path, method
						path = matches[1]
						method = strings.ToUpper(matches[2])
					} else if strings.Contains(line, "@") && strings.Contains(line, ".route") && len(matches) == 2 {
						// Flask simple route (no method specified)
						method = "GET" // Flask defaults to GET
						path = matches[1]
					} else if len(matches) >= 3 {
						// FastAPI/Flask: @app.get('/path')
						// Pattern captures: method, path
						method = strings.ToUpper(matches[1])
						path = matches[2]
					} else if strings.Contains(line, "path(") || strings.Contains(line, "re_path(") {
						// Django path/re_path - no method in pattern
						method = "GET" // Default (Django views specify method in view function)
						path = matches[1]
					} else {
						continue
					}
				} else if ext == ".go" {
					// Go patterns
					if len(matches) >= 3 {
						method = strings.ToUpper(matches[1])
						path = matches[2]
					} else if len(matches) == 2 {
						// HandleFunc - no method specified
						method = "ANY"
						path = matches[1]
					}
				} else if ext == ".cs" {
					// C# patterns
					if len(matches) >= 3 {
						// [HttpGet(...)] format
						method = strings.ToUpper(strings.TrimPrefix(matches[1], "Http"))
						path = matches[2]
					} else if len(matches) == 2 {
						// [Route(...)] format  - no method specified
						method = "ANY"
						path = matches[1]
					}
				} else {
					// JavaScript/TypeScript and others
					if len(matches) >= 3 {
						method = strings.ToUpper(matches[1])
						path = matches[2]
					} else {
						continue
					}
				}

				// Skip invalid paths (empty paths are valid for decorators like @Get() in NestJS)
				// For TypeScript/JS, allow empty paths; for others, skip
				if path == "" && !strings.Contains(ext, ".ts") && !strings.Contains(ext, ".js") && !strings.Contains(ext, ".tsx") && !strings.Contains(ext, ".jsx") {
					continue
				}

				// Generate endpoint ID
				endpointID := fmt.Sprintf("%s-%s-%d", scanID(filePath), method, lineNum)

				found = append(found, Endpoint{
					ID:         endpointID,
					Path:       path,
					Method:     method,
					FilePath:   filePath,
					LineNumber: lineNum,
					Tags:       []string{extractTag(filePath)},
				})

				// Break after finding first match to avoid duplicate endpoints from multiple patterns
				break
			}
		}
	}

	return found
}

// Helper function to generate scan ID from file path
func scanID(filePath string) string {
	return strings.ReplaceAll(filepath.Base(filePath), ".", "-")
}

// Helper function to extract tag from file path
func extractTag(filePath string) string {
	dir := filepath.Dir(filePath)
	if dir == "." || dir == "/" {
		return "api"
	}
	return filepath.Base(dir)
}
