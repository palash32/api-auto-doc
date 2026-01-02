package scanner

import (
	"testing"
)

// Test data for pattern matching
const (
	// Python samples
	pythonFastAPI = `from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
async def get_users():
    return {"users": []}

@app.post("/users/{user_id}")
async def create_user(user_id: int):
    return {"id": user_id}
`

	pythonFlask = `from flask import Flask, Blueprint

bp = Blueprint('api', __name__)

@bp.route('/products', methods=['GET', 'POST'])
def products():
    return {"products": []}

@bp.route('/orders/<int:order_id>')
def get_order(order_id):
    return {"order_id": order_id}
`

	pythonDjango = `from django.urls import path
from . import views

urlpatterns = [
    path('api/items/', views.list_items),
    path('api/items/<int:pk>/', views.get_item),
]
`

	// JavaScript/TypeScript samples
	jsExpress = `const express = require('express');
const router = express.Router();

router.get('/api/customers', (req, res) => {
    res.json({customers: []});
});

router.post('/api/customers/:id', (req, res) => {
    res.json({id: req.params.id});
});

module.exports = router;
`

	tsNestJS = `import { Controller, Get, Post, Param } from '@nestjs/common';

@Controller('api/books')
export class BooksController {
    @Get()
    findAll() {
        return [];
    }

    @Post(':id')
    create(@Param('id') id: string) {
        return { id };
    }
}
`

	jsFastify = `const fastify = require('fastify')();

fastify.get('/api/health', async (request, reply) => {
    return { status: 'ok' };
});

fastify.post('/api/data', async (request, reply) => {
    return { received: true };
});
`

	// Go samples
	goGin = `package main

import "github.com/gin-gonic/gin"

func setupRouter() *gin.Engine {
    r := gin.Default()
    
    r.GET("/api/status", func(c *gin.Context) {
        c.JSON(200, gin.H{"status": "ok"})
    })
    
    r.POST("/api/submit", func(c *gin.Context) {
        c.JSON(200, gin.H{"success": true})
    })
    
    return r
}
`

	goEcho = `package main

import "github.com/labstack/echo/v4"

func main() {
    e := echo.New()
    
    e.GET("/users", getUsers)
    e.POST("/users/:id", createUser)
    
    e.Start(":8080")
}
`

	goStdLib = `package main

import "net/http"

func main() {
    http.HandleFunc("/api/test", handleTest)
    http.HandleFunc("/api/data", handleData)
    http.ListenAndServe(":8080", nil)
}
`

	// Java samples
	javaSpring = `package com.example.api;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class UserController {
    
    @GetMapping("/users")
    public List<User> getUsers() {
        return users;
    }
    
    @PostMapping(value = "/users/{id}")
    public User createUser(@PathVariable Long id) {
        return new User(id);
    }
    
    @PutMapping("/users/{id}")
    public User updateUser(@PathVariable Long id) {
        return new User(id);
    }
}
`

	// C# samples
	csharpASPNet = `using Microsoft.AspNetCore.Mvc;

namespace API.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class ProductsController : ControllerBase
    {
        [HttpGet]
        public IActionResult GetAll()
        {
            return Ok(products);
        }
        
        [HttpPost("{id}")]
        public IActionResult Create(int id)
        {
            return Ok(new { id });
        }
        
        [HttpPut("{id}")]
        public IActionResult Update(int id)
        {
            return Ok();
        }
    }
}
`

	// Non-API files (should not have indicators)
	pythonModel = `from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
`

	jsUtil = `export function formatDate(date) {
    return date.toISOString();
}

export function parseJSON(str) {
    return JSON.parse(str);
}
`

	goConfig = `package config

type Config struct {
    Database string
    Port     int
    Host     string
}

func Load() *Config {
    return &Config{
        Database: "postgres",
        Port:     5432,
    }
}
`
)

// TestHasAPIIndicators tests the Stage 1 pre-filtering
func TestHasAPIIndicators(t *testing.T) {
	tests := []struct {
		name     string
		filePath string
		content  string
		want     bool
	}{
		// Python tests
		{"Python FastAPI", "routes/users.py", pythonFastAPI, true},
		{"Python Flask", "api/products.py", pythonFlask, true},
		{"Python Django", "urls.py", pythonDjango, true},
		{"Python Model", "models/user.py", pythonModel, false},

		// JavaScript/TypeScript tests
		{"JS Express", "routes/customers.js", jsExpress, true},
		{"TS NestJS", "controllers/books.ts", tsNestJS, true},
		{"JS Fastify", "app.js", jsFastify, true},
		{"JS Util", "utils/helpers.js", jsUtil, false},

		// Go tests
		{"Go Gin", "main.go", goGin, true},
		{"Go Echo", "server.go", goEcho, true},
		{"Go Stdlib", "handlers.go", goStdLib, true},
		{"Go Config", "config/config.go", goConfig, false},

		// Java tests
		{"Java Spring", "UserController.java", javaSpring, true},

		// C# tests
		{"C# ASP.NET", "ProductsController.cs", csharpASPNet, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := hasAPIIndicators(tt.filePath, tt.content)
			if got != tt.want {
				t.Errorf("hasAPIIndicators() = %v, want %v", got, tt.want)
			}
		})
	}
}

// TestScanFile tests the Stage 2 deep extraction
func TestScanFile(t *testing.T) {
	tests := []struct {
		name          string
		filePath      string
		content       string
		wantEndpoints int
		checkFirst    *Endpoint // Optional: check first endpoint details
	}{
		{
			name:          "Python FastAPI",
			filePath:      "routes/users.py",
			content:       pythonFastAPI,
			wantEndpoints: 2,
			checkFirst: &Endpoint{
				Path:   "/users",
				Method: "GET",
			},
		},
		{
			name:          "Python Flask",
			filePath:      "api/products.py",
			content:       pythonFlask,
			wantEndpoints: 2,
			checkFirst: &Endpoint{
				Path:   "/products",
				Method: "GET",
			},
		},
		{
			name:          "TS NestJS",
			filePath:      "controllers/books.ts",
			content:       tsNestJS,
			wantEndpoints: 2,
			checkFirst: &Endpoint{
				Method: "GET",
			},
		},
		{
			name:          "Go Gin",
			filePath:      "main.go",
			content:       goGin,
			wantEndpoints: 2,
			checkFirst: &Endpoint{
				Path:   "/api/status",
				Method: "GET",
			},
		},
		{
			name:          "Java Spring",
			filePath:      "UserController.java",
			content:       javaSpring,
			wantEndpoints: 3,
			checkFirst: &Endpoint{
				Path:   "/users",
				Method: "GET", // Corrected: GetMapping -> GET
			},
		},
		{
			name:          "Non-API Python Model",
			filePath:      "models/user.py",
			content:       pythonModel,
			wantEndpoints: 0,
		},
		{
			name:          "Non-API JS Util",
			filePath:      "utils/helpers.js",
			content:       jsUtil,
			wantEndpoints: 0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			endpoints := ScanFile(tt.filePath, tt.content)

			if len(endpoints) != tt.wantEndpoints {
				t.Errorf("ScanFile() found %d endpoints, want %d", len(endpoints), tt.wantEndpoints)
			}

			if tt.checkFirst != nil && len(endpoints) > 0 {
				first := endpoints[0]
				if tt.checkFirst.Path != "" && first.Path != tt.checkFirst.Path {
					t.Errorf("First endpoint path = %v, want %v", first.Path, tt.checkFirst.Path)
				}
				if tt.checkFirst.Method != "" && first.Method != tt.checkFirst.Method {
					t.Errorf("First endpoint method = %v, want %v", first.Method, tt.checkFirst.Method)
				}
			}
		})
	}
}

// TestPythonPatternVariations tests flexible Python patterns
func TestPythonPatternVariations(t *testing.T) {
	variations := []string{
		`@app.get("/test")`,
		`@router.get("/test")`,
		`@api.get("/test")`,
		`@my_router.post("/test")`,
		`@custom_app.delete("/test")`,
	}

	for _, code := range variations {
		t.Run(code, func(t *testing.T) {
			if !hasAPIIndicators("test.py", code) {
				t.Errorf("Failed to detect API indicator in: %s", code)
			}

			endpoints := ScanFile("test.py", code)
			if len(endpoints) == 0 {
				t.Errorf("Failed to extract endpoint from: %s", code)
			}
		})
	}
}

// TestJavaScriptPatternVariations tests flexible JS/TS patterns
func TestJavaScriptPatternVariations(t *testing.T) {
	variations := []string{
		`app.get("/test", handler)`,
		`router.post("/test", handler)`,
		`myRouter.put("/test", handler)`,
		`customApp.delete("/test", handler)`,
		`server.patch("/test", handler)`,
	}

	for _, code := range variations {
		t.Run(code, func(t *testing.T) {
			if !hasAPIIndicators("test.js", code) {
				t.Errorf("Failed to detect API indicator in: %s", code)
			}

			endpoints := ScanFile("test.js", code)
			if len(endpoints) == 0 {
				t.Errorf("Failed to extract endpoint from: %s", code)
			}
		})
	}
}

// BenchmarkHasAPIIndicators benchmarks the pre-filtering performance
func BenchmarkHasAPIIndicators(b *testing.B) {
	for i := 0; i < b.N; i++ {
		hasAPIIndicators("test.py", pythonFastAPI)
	}
}

// BenchmarkScanFile benchmarks the deep extraction performance
func BenchmarkScanFile(b *testing.B) {
	for i := 0; i < b.N; i++ {
		ScanFile("test.py", pythonFastAPI)
	}
}

// TestExcludedDirectories verifies excluded directory names
func TestExcludedDirectories(t *testing.T) {
	excluded := []string{
		"node_modules",
		".git",
		"vendor",
		"__pycache__",
		"venv",
		".venv",
		"dist",
		"build",
	}

	for _, dir := range excluded {
		if !excludedDirs[dir] {
			t.Errorf("Directory %s should be excluded", dir)
		}
	}
}

// TestSupportedExtensions verifies supported file extensions
func TestSupportedExtensions(t *testing.T) {
	supported := []string{
		".py", ".js", ".ts", ".jsx", ".tsx",
		".go", ".java", ".cs",
	}

	for _, ext := range supported {
		if !supportedExtensions[ext] {
			t.Errorf("Extension %s should be supported", ext)
		}
	}
}

// TestExtractTag tests the tag extraction helper
func TestExtractTag(t *testing.T) {
	tests := []struct {
		filePath string
		want     string
	}{
		{"routes/users.py", "routes"},
		{"api/controllers/products.ts", "controllers"},
		{"handlers.go", "api"},
		{"./test.py", "api"},
	}

	for _, tt := range tests {
		t.Run(tt.filePath, func(t *testing.T) {
			got := extractTag(tt.filePath)
			if got != tt.want {
				t.Errorf("extractTag(%s) = %v, want %v", tt.filePath, got, tt.want)
			}
		})
	}
}
