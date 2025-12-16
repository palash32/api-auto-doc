'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { z } from 'zod';
import { Loader2, Eye, EyeOff, Github, Mail, Lock, User, ArrowRight, Check, X } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api';
import { GlassCard } from '@/components/ui/glass-card';

// Zod validation schema matching backend requirements
const signUpSchema = z.object({
    full_name: z.string()
        .min(2, 'Name must be at least 2 characters')
        .max(100, 'Name must be less than 100 characters')
        .trim(),
    email: z.string().email('Please enter a valid email address'),
    password: z.string()
        .min(8, 'Password must be at least 8 characters')
        .max(128, 'Password must be less than 128 characters')
        .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
        .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
        .regex(/\d/, 'Password must contain at least one digit'),
    confirmPassword: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
});

type SignUpFormData = z.infer<typeof signUpSchema>;

// Password requirement checker
const passwordRequirements = [
    { id: 'length', label: 'At least 8 characters', check: (v: string) => v.length >= 8 },
    { id: 'upper', label: 'One uppercase letter', check: (v: string) => /[A-Z]/.test(v) },
    { id: 'lower', label: 'One lowercase letter', check: (v: string) => /[a-z]/.test(v) },
    { id: 'digit', label: 'One digit', check: (v: string) => /\d/.test(v) },
];

export default function SignUpPage() {
    const router = useRouter();
    const [formData, setFormData] = useState<SignUpFormData>({ full_name: '', email: '', password: '', confirmPassword: '' });
    const [errors, setErrors] = useState<Partial<Record<keyof SignUpFormData, string>>>({});
    const [loading, setLoading] = useState(false);
    const [apiError, setApiError] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [passwordFocused, setPasswordFocused] = useState(false);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        // Clear error on change
        if (errors[name as keyof SignUpFormData]) {
            setErrors(prev => ({ ...prev, [name]: undefined }));
        }
        setApiError('');
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setApiError('');

        // Validate with Zod
        const result = signUpSchema.safeParse(formData);
        if (!result.success) {
            const fieldErrors: Partial<Record<keyof SignUpFormData, string>> = {};
            result.error.errors.forEach(err => {
                if (err.path[0]) {
                    fieldErrors[err.path[0] as keyof SignUpFormData] = err.message;
                }
            });
            setErrors(fieldErrors);
            return;
        }

        setLoading(true);

        try {
            const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });

            if (!res.ok) {
                const error = await res.json();
                throw new Error(error.detail || 'Registration failed');
            }

            const data = await res.json();

            // Store token
            localStorage.setItem('token', data.access_token);
            document.cookie = `token=${data.access_token}; path=/; max-age=86400; SameSite=Lax`;

            // Redirect to dashboard
            router.push('/dashboard');
        } catch (err) {
            setApiError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    const handleGitHubLogin = () => {
        window.location.href = `${API_BASE_URL}/api/auth/github/login`;
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-black p-4">
            {/* Background gradient */}
            <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-black to-blue-900/20" />

            <GlassCard className="relative w-full max-w-md p-8">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-white mb-2">Create Account</h1>
                    <p className="text-white/60">Start documenting your APIs today</p>
                </div>

                {/* GitHub Signup Button */}
                <button
                    onClick={handleGitHubLogin}
                    className="w-full flex items-center justify-center gap-3 px-4 py-3 mb-6 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-all text-white"
                >
                    <Github size={20} />
                    <span>Continue with GitHub</span>
                </button>

                <div className="relative mb-6">
                    <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-white/10" />
                    </div>
                    <div className="relative flex justify-center text-sm">
                        <span className="px-4 bg-[#0a0a0a] text-white/40">or sign up with email</span>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                    {/* Full Name */}
                    <div>
                        <label className="block text-sm font-medium text-white/70 mb-1.5">Full Name</label>
                        <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" size={18} />
                            <input
                                type="text"
                                name="full_name"
                                value={formData.full_name}
                                onChange={handleChange}
                                placeholder="John Doe"
                                className={`w-full pl-10 pr-4 py-3 rounded-lg bg-white/5 border ${errors.full_name ? 'border-red-500' : 'border-white/10'
                                    } text-white placeholder-white/30 focus:outline-none focus:border-purple-500 transition-all`}
                            />
                        </div>
                        {errors.full_name && <p className="mt-1 text-sm text-red-400">{errors.full_name}</p>}
                    </div>

                    {/* Email */}
                    <div>
                        <label className="block text-sm font-medium text-white/70 mb-1.5">Email</label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" size={18} />
                            <input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleChange}
                                placeholder="you@example.com"
                                className={`w-full pl-10 pr-4 py-3 rounded-lg bg-white/5 border ${errors.email ? 'border-red-500' : 'border-white/10'
                                    } text-white placeholder-white/30 focus:outline-none focus:border-purple-500 transition-all`}
                            />
                        </div>
                        {errors.email && <p className="mt-1 text-sm text-red-400">{errors.email}</p>}
                    </div>

                    {/* Password */}
                    <div>
                        <label className="block text-sm font-medium text-white/70 mb-1.5">Password</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" size={18} />
                            <input
                                type={showPassword ? 'text' : 'password'}
                                name="password"
                                value={formData.password}
                                onChange={handleChange}
                                onFocus={() => setPasswordFocused(true)}
                                onBlur={() => setPasswordFocused(false)}
                                placeholder="••••••••"
                                className={`w-full pl-10 pr-12 py-3 rounded-lg bg-white/5 border ${errors.password ? 'border-red-500' : 'border-white/10'
                                    } text-white placeholder-white/30 focus:outline-none focus:border-purple-500 transition-all`}
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60"
                            >
                                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>

                        {/* Password Requirements */}
                        {(passwordFocused || formData.password.length > 0) && (
                            <div className="mt-2 p-3 rounded-lg bg-white/5 border border-white/10">
                                <p className="text-xs text-white/50 mb-2">Password must contain:</p>
                                <div className="grid grid-cols-2 gap-1">
                                    {passwordRequirements.map(req => {
                                        const met = req.check(formData.password);
                                        return (
                                            <div key={req.id} className="flex items-center gap-1.5">
                                                {met ? (
                                                    <Check size={12} className="text-green-400" />
                                                ) : (
                                                    <X size={12} className="text-white/30" />
                                                )}
                                                <span className={`text-xs ${met ? 'text-green-400' : 'text-white/40'}`}>
                                                    {req.label}
                                                </span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}
                        {errors.password && <p className="mt-1 text-sm text-red-400">{errors.password}</p>}
                    </div>

                    {/* Confirm Password */}
                    <div>
                        <label className="block text-sm font-medium text-white/70 mb-1.5">Confirm Password</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" size={18} />
                            <input
                                type={showPassword ? 'text' : 'password'}
                                name="confirmPassword"
                                value={formData.confirmPassword}
                                onChange={handleChange}
                                placeholder="••••••••"
                                className={`w-full pl-10 pr-4 py-3 rounded-lg bg-white/5 border ${errors.confirmPassword ? 'border-red-500' : 'border-white/10'
                                    } text-white placeholder-white/30 focus:outline-none focus:border-purple-500 transition-all`}
                            />
                        </div>
                        {errors.confirmPassword && <p className="mt-1 text-sm text-red-400">{errors.confirmPassword}</p>}
                    </div>

                    {/* API Error */}
                    {apiError && (
                        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                            {apiError}
                        </div>
                    )}

                    {/* Submit Button */}
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? (
                            <>
                                <Loader2 size={18} className="animate-spin" />
                                <span>Creating account...</span>
                            </>
                        ) : (
                            <>
                                <span>Create Account</span>
                                <ArrowRight size={18} />
                            </>
                        )}
                    </button>
                </form>

                <p className="mt-6 text-center text-white/60">
                    Already have an account?{' '}
                    <Link href="/auth/signin" className="text-purple-400 hover:text-purple-300 transition-colors">
                        Sign in
                    </Link>
                </p>
            </GlassCard>
        </div>
    );
}
