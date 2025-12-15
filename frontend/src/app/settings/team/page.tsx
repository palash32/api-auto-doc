"use client";

import React, { useState, useEffect } from "react";
import {
    Users,
    Plus,
    Mail,
    Shield,
    Edit2,
    Trash2,
    Check,
    X,
    Crown,
    UserCog,
    Code,
    Eye,
    ChevronDown,
    Folder,
    Search
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE_URL } from "@/lib/api";
import { GlassCard } from "@/components/ui/glass-card";

interface TeamMember {
    id: string;
    user_id: string;
    email: string;
    full_name: string | null;
    role: string;
    is_active: boolean;
    invited_at: string;
    accepted_at: string | null;
}

interface Workspace {
    id: string;
    name: string;
    slug: string;
    description: string | null;
    icon: string | null;
    color: string | null;
    is_default: boolean;
    is_private: boolean;
}

const ROLE_INFO = {
    owner: { icon: Crown, label: "Owner", color: "text-amber-400", bg: "bg-amber-500/10" },
    admin: { icon: UserCog, label: "Admin", color: "text-purple-400", bg: "bg-purple-500/10" },
    developer: { icon: Code, label: "Developer", color: "text-blue-400", bg: "bg-blue-500/10" },
    viewer: { icon: Eye, label: "Viewer", color: "text-gray-400", bg: "bg-gray-500/10" }
};

export default function TeamSettingsPage() {
    const [activeTab, setActiveTab] = useState<"members" | "workspaces">("members");
    const [members, setMembers] = useState<TeamMember[]>([]);
    const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
    const [loading, setLoading] = useState(true);
    const [showInviteModal, setShowInviteModal] = useState(false);
    const [showWorkspaceModal, setShowWorkspaceModal] = useState(false);
    const [inviteEmail, setInviteEmail] = useState("");
    const [inviteRole, setInviteRole] = useState("developer");
    const [searchQuery, setSearchQuery] = useState("");
    const [newWorkspaceName, setNewWorkspaceName] = useState("");
    const [newWorkspaceDescription, setNewWorkspaceDescription] = useState("");

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [membersRes, workspacesRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/team/members`),
                fetch(`${API_BASE_URL}/api/team/workspaces`)
            ]);

            if (membersRes.ok) {
                setMembers(await membersRes.json());
            }
            if (workspacesRes.ok) {
                setWorkspaces(await workspacesRes.json());
            }
        } catch (e) {
            console.error("Failed to fetch team data:", e);
        } finally {
            setLoading(false);
        }
    };

    const inviteMember = async () => {
        if (!inviteEmail) return;

        try {
            const res = await fetch(`${API_BASE_URL}/api/team/members`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: inviteEmail, role: inviteRole })
            });

            if (res.ok) {
                setShowInviteModal(false);
                setInviteEmail("");
                fetchData();
            }
        } catch (e) {
            console.error("Failed to invite member:", e);
        }
    };

    const updateRole = async (memberId: string, role: string) => {
        try {
            await fetch(`${API_BASE_URL}/api/team/members/${memberId}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ role })
            });
            fetchData();
        } catch (e) {
            console.error("Failed to update role:", e);
        }
    };

    const removeMember = async (memberId: string) => {
        if (!confirm("Are you sure you want to remove this member?")) return;

        try {
            await fetch(`${API_BASE_URL}/api/team/members/${memberId}`, {
                method: "DELETE"
            });
            fetchData();
        } catch (e) {
            console.error("Failed to remove member:", e);
        }
    };

    const createWorkspace = async () => {
        if (!newWorkspaceName) return;

        try {
            const res = await fetch(`${API_BASE_URL}/api/team/workspaces`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: newWorkspaceName,
                    description: newWorkspaceDescription,
                    slug: newWorkspaceName.toLowerCase().replace(/\s+/g, '-')
                })
            });

            if (res.ok) {
                setShowWorkspaceModal(false);
                setNewWorkspaceName("");
                setNewWorkspaceDescription("");
                fetchData();
            }
        } catch (e) {
            console.error("Failed to create workspace:", e);
        }
    };

    const filteredMembers = members.filter(m =>
        m.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        m.full_name?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            {/* Header */}
            <header className="border-b border-white/10 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-6 py-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
                            <Users size={20} />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold">Team Settings</h1>
                            <p className="text-xs text-gray-500">Manage members, roles, and workspaces</p>
                        </div>
                    </div>
                </div>
            </header>

            <div className="max-w-6xl mx-auto p-6">
                {/* Tabs */}
                <div className="flex gap-2 mb-6">
                    <button
                        onClick={() => setActiveTab("members")}
                        className={cn(
                            "px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors",
                            activeTab === "members"
                                ? "bg-white/10 text-white"
                                : "text-gray-400 hover:text-white"
                        )}
                    >
                        <Users size={16} />
                        Members ({members.length})
                    </button>
                    <button
                        onClick={() => setActiveTab("workspaces")}
                        className={cn(
                            "px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors",
                            activeTab === "workspaces"
                                ? "bg-white/10 text-white"
                                : "text-gray-400 hover:text-white"
                        )}
                    >
                        <Folder size={16} />
                        Workspaces ({workspaces.length})
                    </button>
                </div>

                {/* Members Tab */}
                {activeTab === "members" && (
                    <div className="space-y-4">
                        {/* Actions Bar */}
                        <div className="flex items-center gap-4">
                            <div className="relative flex-1 max-w-md">
                                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                                <input
                                    type="text"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    placeholder="Search members..."
                                    className="w-full pl-10 pr-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-purple-500/50"
                                />
                            </div>
                            <button
                                onClick={() => setShowInviteModal(true)}
                                className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg text-sm font-medium flex items-center gap-2 btn-press"
                            >
                                <Plus size={16} />
                                Invite Member
                            </button>
                        </div>

                        {/* Members List */}
                        <GlassCard className="overflow-hidden">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-white/10">
                                        <th className="text-left p-4 text-xs font-medium text-gray-400">MEMBER</th>
                                        <th className="text-left p-4 text-xs font-medium text-gray-400">ROLE</th>
                                        <th className="text-left p-4 text-xs font-medium text-gray-400">STATUS</th>
                                        <th className="text-right p-4 text-xs font-medium text-gray-400">ACTIONS</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredMembers.map((member) => {
                                        const roleInfo = ROLE_INFO[member.role as keyof typeof ROLE_INFO] || ROLE_INFO.viewer;
                                        const RoleIcon = roleInfo.icon;

                                        return (
                                            <tr key={member.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                                <td className="p-4">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-white font-bold">
                                                            {(member.full_name || member.email).charAt(0).toUpperCase()}
                                                        </div>
                                                        <div>
                                                            <p className="font-medium text-sm">{member.full_name || "Pending"}</p>
                                                            <p className="text-xs text-gray-500">{member.email}</p>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="p-4">
                                                    <span className={cn(
                                                        "px-2.5 py-1 rounded-lg text-xs font-medium flex items-center gap-1.5 w-fit",
                                                        roleInfo.bg, roleInfo.color
                                                    )}>
                                                        <RoleIcon size={12} />
                                                        {roleInfo.label}
                                                    </span>
                                                </td>
                                                <td className="p-4">
                                                    {member.accepted_at ? (
                                                        <span className="text-xs text-emerald-400 flex items-center gap-1">
                                                            <Check size={12} />
                                                            Active
                                                        </span>
                                                    ) : (
                                                        <span className="text-xs text-amber-400">Pending</span>
                                                    )}
                                                </td>
                                                <td className="p-4 text-right">
                                                    {member.role !== "owner" && (
                                                        <div className="flex items-center justify-end gap-2">
                                                            <select
                                                                value={member.role}
                                                                onChange={(e) => updateRole(member.id, e.target.value)}
                                                                className="px-2 py-1 rounded bg-white/5 border border-white/10 text-xs cursor-pointer focus:outline-none"
                                                            >
                                                                <option value="admin">Admin</option>
                                                                <option value="developer">Developer</option>
                                                                <option value="viewer">Viewer</option>
                                                            </select>
                                                            <button
                                                                onClick={() => removeMember(member.id)}
                                                                className="p-1.5 text-gray-500 hover:text-red-400 transition-colors"
                                                            >
                                                                <Trash2 size={14} />
                                                            </button>
                                                        </div>
                                                    )}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>

                            {filteredMembers.length === 0 && (
                                <div className="p-8 text-center text-gray-500">
                                    {searchQuery ? "No members found" : "No team members yet"}
                                </div>
                            )}
                        </GlassCard>
                    </div>
                )}

                {/* Workspaces Tab */}
                {activeTab === "workspaces" && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {workspaces.map((ws) => (
                            <GlassCard key={ws.id} className="p-4 hover:border-white/20 transition-colors cursor-pointer">
                                <div className="flex items-center gap-3 mb-2">
                                    <div
                                        className="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
                                        style={{ backgroundColor: ws.color || "#3B82F6" + "20" }}
                                    >
                                        {ws.icon || "📁"}
                                    </div>
                                    <div>
                                        <h3 className="font-medium">{ws.name}</h3>
                                        <p className="text-xs text-gray-500">/{ws.slug}</p>
                                    </div>
                                </div>
                                {ws.description && (
                                    <p className="text-sm text-gray-400 line-clamp-2">{ws.description}</p>
                                )}
                                <div className="flex items-center gap-2 mt-3">
                                    {ws.is_default && (
                                        <span className="text-[10px] px-2 py-0.5 bg-blue-500/10 text-blue-400 rounded">Default</span>
                                    )}
                                    {ws.is_private && (
                                        <span className="text-[10px] px-2 py-0.5 bg-amber-500/10 text-amber-400 rounded">Private</span>
                                    )}
                                </div>
                            </GlassCard>
                        ))}

                        {/* Add Workspace Card */}
                        <button
                            onClick={() => setShowWorkspaceModal(true)}
                            className="p-4 border-2 border-dashed border-white/10 rounded-xl hover:border-white/20 transition-colors flex flex-col items-center justify-center gap-2 text-gray-500 hover:text-white min-h-[120px]"
                        >
                            <Plus size={24} />
                            <span className="text-sm">Create Workspace</span>
                        </button>
                    </div>
                )}
            </div>

            {/* Invite Modal */}
            {showInviteModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
                    <GlassCard className="w-full max-w-md p-6">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-lg font-semibold">Invite Team Member</h2>
                            <button
                                onClick={() => setShowInviteModal(false)}
                                className="p-1 hover:bg-white/10 rounded-lg"
                            >
                                <X size={18} />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Email Address</label>
                                <div className="relative">
                                    <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                                    <input
                                        type="email"
                                        value={inviteEmail}
                                        onChange={(e) => setInviteEmail(e.target.value)}
                                        placeholder="colleague@company.com"
                                        className="w-full pl-10 pr-4 py-3 rounded-lg bg-white/5 border border-white/10 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-purple-500/50"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Role</label>
                                <select
                                    value={inviteRole}
                                    onChange={(e) => setInviteRole(e.target.value)}
                                    className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 focus:outline-none focus:ring-1 focus:ring-purple-500/50"
                                >
                                    <option value="admin">Admin - Can manage members & settings</option>
                                    <option value="developer">Developer - Can edit docs & run scans</option>
                                    <option value="viewer">Viewer - Read-only access</option>
                                </select>
                            </div>

                            <button
                                onClick={inviteMember}
                                disabled={!inviteEmail}
                                className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Mail size={16} />
                                Send Invitation
                            </button>
                        </div>
                    </GlassCard>
                </div>
            )}

            {/* Workspace Modal */}
            {showWorkspaceModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
                    <GlassCard className="w-full max-w-md p-6">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-lg font-semibold">Create Workspace</h2>
                            <button
                                onClick={() => setShowWorkspaceModal(false)}
                                className="p-1 hover:bg-white/10 rounded-lg"
                            >
                                <X size={18} />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Workspace Name</label>
                                <input
                                    type="text"
                                    value={newWorkspaceName}
                                    onChange={(e) => setNewWorkspaceName(e.target.value)}
                                    placeholder="e.g., Backend APIs"
                                    className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-purple-500/50"
                                />
                            </div>

                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Description (optional)</label>
                                <textarea
                                    value={newWorkspaceDescription}
                                    onChange={(e) => setNewWorkspaceDescription(e.target.value)}
                                    placeholder="Describe what this workspace is for..."
                                    rows={3}
                                    className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-purple-500/50 resize-none"
                                />
                            </div>

                            <button
                                onClick={createWorkspace}
                                disabled={!newWorkspaceName}
                                className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Folder size={16} />
                                Create Workspace
                            </button>
                        </div>
                    </GlassCard>
                </div>
            )}
        </div>
    );
}
