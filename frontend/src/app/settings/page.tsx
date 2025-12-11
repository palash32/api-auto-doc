'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import {
    CreditCard,
    Users,
    Shield,
    Building2,
    Palette,
    ChevronRight,
    Settings as SettingsIcon
} from 'lucide-react';

const settingsCategories = [
    {
        title: 'Billing & Plans',
        description: 'Manage your subscription, view invoices, and update payment methods',
        icon: CreditCard,
        href: '/settings/billing',
        color: 'from-green-500 to-emerald-600',
    },
    {
        title: 'Team & Collaboration',
        description: 'Invite team members, manage roles, and configure workspaces',
        icon: Users,
        href: '/settings/team',
        color: 'from-blue-500 to-indigo-600',
    },
    {
        title: 'Security & Compliance',
        description: 'API keys, SSO configuration, audit logs, and access controls',
        icon: Shield,
        href: '/settings/security',
        color: 'from-purple-500 to-violet-600',
    },
    {
        title: 'Enterprise Features',
        description: 'Custom integrations, SLA metrics, and support ticket management',
        icon: Building2,
        href: '/settings/enterprise',
        color: 'from-orange-500 to-red-600',
    },
    {
        title: 'Branding & Customization',
        description: 'Customize your documentation portal with your brand colors and logo',
        icon: Palette,
        href: '/settings/branding',
        color: 'from-pink-500 to-rose-600',
    },
];

export default function SettingsPage() {
    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-12"
                >
                    <div className="flex items-center gap-4 mb-4">
                        <div className="p-3 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600">
                            <SettingsIcon className="w-8 h-8 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-white">Settings</h1>
                            <p className="text-gray-400">Manage your account and organization preferences</p>
                        </div>
                    </div>
                </motion.div>

                {/* Settings Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {settingsCategories.map((category, index) => (
                        <motion.div
                            key={category.title}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                        >
                            <Link href={category.href}>
                                <div className="group relative bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6 hover:border-gray-600 transition-all duration-300 hover:shadow-lg hover:shadow-indigo-500/10">
                                    {/* Gradient accent */}
                                    <div className={`absolute inset-0 bg-gradient-to-br ${category.color} opacity-0 group-hover:opacity-5 rounded-2xl transition-opacity duration-300`} />

                                    <div className="relative flex items-start gap-4">
                                        <div className={`p-3 rounded-xl bg-gradient-to-br ${category.color}`}>
                                            <category.icon className="w-6 h-6 text-white" />
                                        </div>

                                        <div className="flex-1">
                                            <div className="flex items-center justify-between mb-2">
                                                <h3 className="text-lg font-semibold text-white group-hover:text-indigo-400 transition-colors">
                                                    {category.title}
                                                </h3>
                                                <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" />
                                            </div>
                                            <p className="text-sm text-gray-400">
                                                {category.description}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </Link>
                        </motion.div>
                    ))}
                </div>

                {/* Quick Stats */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                    className="mt-12 bg-gray-800/30 rounded-2xl border border-gray-700/50 p-8"
                >
                    <h2 className="text-xl font-semibold text-white mb-6">Account Overview</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                        <div className="text-center">
                            <div className="text-3xl font-bold text-indigo-400">Free</div>
                            <div className="text-sm text-gray-400 mt-1">Current Plan</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-green-400">2</div>
                            <div className="text-sm text-gray-400 mt-1">Repositories</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-blue-400">1</div>
                            <div className="text-sm text-gray-400 mt-1">Team Members</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-purple-400">∞</div>
                            <div className="text-sm text-gray-400 mt-1">API Calls Left</div>
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}
