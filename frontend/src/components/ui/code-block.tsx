"use client";

import React, { useState, useCallback } from "react";
import { Check, Copy, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface CodeBlockProps {
    /** Code examples for different languages */
    examples: {
        language: string;
        label: string;
        code: string;
    }[];
    /** Optional title for the code block */
    title?: string;
    /** Whether to start expanded */
    defaultExpanded?: boolean;
    /** Custom class name */
    className?: string;
}

/**
 * Reusable code block component with:
 * - Language tabs (curl, Python, JavaScript)
 * - Syntax highlighting (basic)
 * - Copy-to-clipboard with success feedback
 * - Dark theme optimized
 */
export const CodeBlock: React.FC<CodeBlockProps> = ({
    examples,
    title,
    defaultExpanded = true,
    className
}) => {
    const [selectedLanguage, setSelectedLanguage] = useState(examples[0]?.language || "curl");
    const [copied, setCopied] = useState(false);
    const [expanded, setExpanded] = useState(defaultExpanded);

    const currentExample = examples.find(e => e.language === selectedLanguage) || examples[0];

    const handleCopy = useCallback(async () => {
        if (!currentExample) return;

        try {
            await navigator.clipboard.writeText(currentExample.code);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error("Failed to copy:", err);
        }
    }, [currentExample]);

    // Basic syntax highlighting
    const highlightCode = (code: string, language: string): React.ReactNode => {
        // Simple regex-based highlighting for common patterns
        const lines = code.split('\n');

        return lines.map((line, idx) => {
            let highlighted = line;

            if (language === "curl" || language === "bash") {
                // Highlight curl commands
                highlighted = line
                    .replace(/(curl|wget|http|https)/gi, '<span class="text-yellow-400">$1</span>')
                    .replace(/(-X|--request|-H|--header|-d|--data)/g, '<span class="text-purple-400">$1</span>')
                    .replace(/(GET|POST|PUT|DELETE|PATCH)/g, '<span class="text-emerald-400 font-bold">$1</span>')
                    .replace(/(".*?")/g, '<span class="text-green-400">$1</span>')
                    .replace(/(https?:\/\/[^\s"']+)/g, '<span class="text-blue-400">$1</span>');
            } else if (language === "python") {
                highlighted = line
                    .replace(/\b(import|from|def|class|return|if|else|elif|for|while|in|as|with|try|except|raise|True|False|None)\b/g, '<span class="text-purple-400">$1</span>')
                    .replace(/\b(requests|json|print)\b/g, '<span class="text-yellow-400">$1</span>')
                    .replace(/(["'].*?["'])/g, '<span class="text-green-400">$1</span>')
                    .replace(/(#.*$)/gm, '<span class="text-gray-500">$1</span>')
                    .replace(/\b(\d+)\b/g, '<span class="text-orange-400">$1</span>');
            } else if (language === "javascript" || language === "typescript") {
                highlighted = line
                    .replace(/\b(const|let|var|function|async|await|return|if|else|for|while|import|from|export|default|try|catch|throw|new|class|extends)\b/g, '<span class="text-purple-400">$1</span>')
                    .replace(/\b(fetch|console|JSON|Promise|Error)\b/g, '<span class="text-yellow-400">$1</span>')
                    .replace(/(["'`].*?["'`])/g, '<span class="text-green-400">$1</span>')
                    .replace(/(\/\/.*$)/gm, '<span class="text-gray-500">$1</span>')
                    .replace(/\b(\d+)\b/g, '<span class="text-orange-400">$1</span>');
            }

            return (
                <div key={idx} className="flex">
                    <span className="select-none text-gray-600 w-8 text-right mr-4 text-xs">
                        {idx + 1}
                    </span>
                    <span
                        className="flex-1"
                        dangerouslySetInnerHTML={{ __html: highlighted }}
                    />
                </div>
            );
        });
    };

    if (!examples || examples.length === 0) {
        return null;
    }

    return (
        <div className={cn("rounded-xl overflow-hidden border border-white/10 bg-[#0A0A0A]", className)}>
            {/* Header with tabs and copy button */}
            <div className="flex items-center justify-between px-4 py-2 bg-white/5 border-b border-white/10">
                <div className="flex items-center gap-2">
                    {title && (
                        <button
                            onClick={() => setExpanded(!expanded)}
                            className="flex items-center gap-2 text-sm font-medium text-gray-300 hover:text-white transition-colors"
                        >
                            <ChevronDown
                                size={16}
                                className={cn(
                                    "transition-transform duration-200",
                                    !expanded && "-rotate-90"
                                )}
                            />
                            {title}
                        </button>
                    )}
                </div>

                {/* Language tabs */}
                <div className="flex items-center gap-1">
                    {examples.map(example => (
                        <button
                            key={example.language}
                            onClick={() => setSelectedLanguage(example.language)}
                            className={cn(
                                "px-3 py-1 rounded-md text-xs font-medium transition-all",
                                selectedLanguage === example.language
                                    ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                                    : "text-gray-400 hover:text-white hover:bg-white/5"
                            )}
                        >
                            {example.label}
                        </button>
                    ))}

                    {/* Copy button */}
                    <button
                        onClick={handleCopy}
                        className={cn(
                            "ml-2 p-1.5 rounded-md transition-all",
                            copied
                                ? "bg-emerald-500/20 text-emerald-400"
                                : "text-gray-400 hover:text-white hover:bg-white/10"
                        )}
                        title={copied ? "Copied!" : "Copy to clipboard"}
                    >
                        {copied ? <Check size={14} /> : <Copy size={14} />}
                    </button>
                </div>
            </div>

            {/* Code content */}
            {expanded && currentExample && (
                <div className="p-4 overflow-x-auto">
                    <pre className="font-mono text-sm leading-relaxed text-gray-300">
                        <code>{highlightCode(currentExample.code, currentExample.language)}</code>
                    </pre>
                </div>
            )}
        </div>
    );
};

/**
 * Helper function to generate code examples for an API endpoint
 */
export function generateCodeExamples(
    method: string,
    path: string,
    baseUrl: string = "https://api.example.com"
): { language: string; label: string; code: string }[] {
    const fullUrl = `${baseUrl}${path}`;
    const hasBody = method === "POST" || method === "PUT" || method === "PATCH";

    return [
        {
            language: "curl",
            label: "cURL",
            code: hasBody
                ? `curl -X ${method} "${fullUrl}" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -d '{
    "key": "value"
  }'`
                : `curl -X ${method} "${fullUrl}" \\
  -H "Authorization: Bearer YOUR_API_KEY"`
        },
        {
            language: "python",
            label: "Python",
            code: hasBody
                ? `import requests

url = "${fullUrl}"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY"
}
data = {
    "key": "value"
}

response = requests.${method.toLowerCase()}(url, json=data, headers=headers)
print(response.json())`
                : `import requests

url = "${fullUrl}"
headers = {
    "Authorization": "Bearer YOUR_API_KEY"
}

response = requests.${method.toLowerCase()}(url, headers=headers)
print(response.json())`
        },
        {
            language: "javascript",
            label: "JavaScript",
            code: hasBody
                ? `const response = await fetch("${fullUrl}", {
  method: "${method}",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY"
  },
  body: JSON.stringify({
    key: "value"
  })
});

const data = await response.json();
console.log(data);`
                : `const response = await fetch("${fullUrl}", {
  method: "${method}",
  headers: {
    "Authorization": "Bearer YOUR_API_KEY"
  }
});

const data = await response.json();
console.log(data);`
        }
    ];
}
