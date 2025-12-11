"use client";

import React, { useState, useEffect } from "react";
import {
    CreditCard,
    Package,
    Receipt,
    TrendingUp,
    Check,
    AlertTriangle,
    Plus,
    Trash2,
    Crown,
    Zap,
    Building,
    Star
} from "lucide-react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui/glass-card";

interface Plan {
    id: string;
    name: string;
    tier: string;
    description: string | null;
    price_monthly: number;
    price_yearly: number;
    currency: string;
    max_repositories: number;
    max_endpoints: number;
    max_team_members: number;
    features: string[] | null;
}

interface Subscription {
    id: string;
    plan: Plan;
    billing_interval: string;
    status: string;
    current_period_end: string | null;
    cancel_at_period_end: boolean;
}

interface Invoice {
    id: string;
    invoice_number: string;
    total: number;
    status: string;
    invoice_date: string;
    stripe_pdf_url: string | null;
}

interface PaymentMethod {
    id: string;
    card_brand: string | null;
    card_last4: string | null;
    card_exp_month: number | null;
    card_exp_year: number | null;
    is_default: boolean;
}

const TIER_ICONS: Record<string, any> = {
    free: Star,
    starter: Zap,
    pro: Crown,
    enterprise: Building
};

const TIER_COLORS: Record<string, string> = {
    free: "from-gray-500 to-gray-600",
    starter: "from-blue-500 to-cyan-500",
    pro: "from-purple-500 to-pink-500",
    enterprise: "from-amber-500 to-orange-500"
};

export default function BillingPage() {
    const [plans, setPlans] = useState<Plan[]>([]);
    const [subscription, setSubscription] = useState<Subscription | null>(null);
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
    const [loading, setLoading] = useState(true);
    const [billingInterval, setBillingInterval] = useState<"monthly" | "yearly">("monthly");

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [plansRes, subRes, invoicesRes, methodsRes] = await Promise.all([
                fetch("http://localhost:8000/api/billing/plans"),
                fetch("http://localhost:8000/api/billing/subscription"),
                fetch("http://localhost:8000/api/billing/invoices"),
                fetch("http://localhost:8000/api/billing/payment-methods")
            ]);

            if (plansRes.ok) setPlans(await plansRes.json());
            if (subRes.ok) {
                const data = await subRes.json();
                if (data) setSubscription(data);
            }
            if (invoicesRes.ok) setInvoices(await invoicesRes.json());
            if (methodsRes.ok) setPaymentMethods(await methodsRes.json());
        } catch (e) {
            console.error("Failed to fetch billing data:", e);
        } finally {
            setLoading(false);
        }
    };

    const subscribe = async (planId: string) => {
        try {
            const res = await fetch("http://localhost:8000/api/billing/subscription", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ plan_id: planId, billing_interval: billingInterval })
            });
            if (res.ok) {
                fetchData();
            }
        } catch (e) {
            console.error("Failed to subscribe:", e);
        }
    };

    const cancelSubscription = async () => {
        if (!confirm("Are you sure you want to cancel your subscription?")) return;
        try {
            await fetch("http://localhost:8000/api/billing/subscription/cancel", {
                method: "POST"
            });
            fetchData();
        } catch (e) {
            console.error("Failed to cancel:", e);
        }
    };

    const formatCurrency = (amount: number, currency: string = "USD") => {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency
        }).format(amount);
    };

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric"
        });
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
                <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            {/* Header */}
            <header className="border-b border-white/10 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-6 py-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
                            <CreditCard size={20} />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold">Billing & Plans</h1>
                            <p className="text-xs text-gray-500">Manage your subscription and payments</p>
                        </div>
                    </div>
                </div>
            </header>

            <div className="max-w-6xl mx-auto p-6 space-y-8">
                {/* Current Plan */}
                {subscription && (
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <Package size={14} className="text-purple-400" />
                            Current Plan
                        </h3>

                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className={cn(
                                    "w-12 h-12 rounded-xl bg-gradient-to-br flex items-center justify-center",
                                    TIER_COLORS[subscription.plan.tier]
                                )}>
                                    {React.createElement(
                                        TIER_ICONS[subscription.plan.tier] || Star,
                                        { size: 24 }
                                    )}
                                </div>
                                <div>
                                    <p className="text-xl font-bold">{subscription.plan.name}</p>
                                    <p className="text-sm text-gray-400">
                                        {formatCurrency(
                                            subscription.billing_interval === "monthly"
                                                ? subscription.plan.price_monthly
                                                : subscription.plan.price_yearly
                                        )}
                                        /{subscription.billing_interval === "monthly" ? "mo" : "yr"}
                                    </p>
                                </div>
                            </div>

                            <div className="text-right">
                                <p className={cn(
                                    "text-sm px-2 py-1 rounded",
                                    subscription.status === "active"
                                        ? "bg-emerald-500/10 text-emerald-400"
                                        : "bg-amber-500/10 text-amber-400"
                                )}>
                                    {subscription.status}
                                </p>
                                {subscription.current_period_end && (
                                    <p className="text-xs text-gray-500 mt-1">
                                        Renews {formatDate(subscription.current_period_end)}
                                    </p>
                                )}
                            </div>
                        </div>

                        {subscription.plan.tier !== "free" && (
                            <button
                                onClick={cancelSubscription}
                                className="mt-4 text-xs text-gray-500 hover:text-red-400"
                            >
                                Cancel subscription
                            </button>
                        )}
                    </GlassCard>
                )}

                {/* Billing Interval Toggle */}
                <div className="flex justify-center">
                    <div className="bg-white/5 rounded-full p-1 flex">
                        <button
                            onClick={() => setBillingInterval("monthly")}
                            className={cn(
                                "px-4 py-2 rounded-full text-sm transition-colors",
                                billingInterval === "monthly"
                                    ? "bg-purple-500 text-white"
                                    : "text-gray-400 hover:text-white"
                            )}
                        >
                            Monthly
                        </button>
                        <button
                            onClick={() => setBillingInterval("yearly")}
                            className={cn(
                                "px-4 py-2 rounded-full text-sm transition-colors",
                                billingInterval === "yearly"
                                    ? "bg-purple-500 text-white"
                                    : "text-gray-400 hover:text-white"
                            )}
                        >
                            Yearly <span className="text-emerald-400 text-xs">Save 20%</span>
                        </button>
                    </div>
                </div>

                {/* Plans Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {plans.map((plan) => (
                        <GlassCard
                            key={plan.id}
                            className={cn(
                                "p-6 relative",
                                subscription?.plan.id === plan.id && "ring-2 ring-purple-500"
                            )}
                        >
                            {plan.tier === "pro" && (
                                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full text-xs font-medium">
                                    Popular
                                </div>
                            )}

                            <div className={cn(
                                "w-10 h-10 rounded-lg bg-gradient-to-br flex items-center justify-center mb-4",
                                TIER_COLORS[plan.tier]
                            )}>
                                {React.createElement(TIER_ICONS[plan.tier] || Star, { size: 20 })}
                            </div>

                            <h3 className="text-lg font-bold">{plan.name}</h3>
                            <p className="text-xs text-gray-500 mb-4">{plan.description}</p>

                            <div className="mb-4">
                                <span className="text-3xl font-bold">
                                    {formatCurrency(
                                        billingInterval === "monthly" ? plan.price_monthly : plan.price_yearly
                                    )}
                                </span>
                                <span className="text-gray-500 text-sm">
                                    /{billingInterval === "monthly" ? "mo" : "yr"}
                                </span>
                            </div>

                            <ul className="space-y-2 mb-6">
                                <li className="text-xs flex items-center gap-2">
                                    <Check size={12} className="text-emerald-400" />
                                    {plan.max_repositories === -1 ? "Unlimited" : plan.max_repositories} repositories
                                </li>
                                <li className="text-xs flex items-center gap-2">
                                    <Check size={12} className="text-emerald-400" />
                                    {plan.max_endpoints === -1 ? "Unlimited" : plan.max_endpoints} endpoints
                                </li>
                                <li className="text-xs flex items-center gap-2">
                                    <Check size={12} className="text-emerald-400" />
                                    {plan.max_team_members === -1 ? "Unlimited" : plan.max_team_members} team members
                                </li>
                                {plan.features?.slice(0, 3).map((feature, i) => (
                                    <li key={i} className="text-xs flex items-center gap-2">
                                        <Check size={12} className="text-emerald-400" />
                                        {feature}
                                    </li>
                                ))}
                            </ul>

                            <button
                                onClick={() => subscribe(plan.id)}
                                disabled={subscription?.plan.id === plan.id}
                                className={cn(
                                    "w-full py-2 rounded-lg text-sm font-medium transition-colors",
                                    subscription?.plan.id === plan.id
                                        ? "bg-white/10 text-gray-500 cursor-not-allowed"
                                        : "bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90"
                                )}
                            >
                                {subscription?.plan.id === plan.id ? "Current Plan" : "Select Plan"}
                            </button>
                        </GlassCard>
                    ))}
                </div>

                {/* Payment Methods & Invoices */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Payment Methods */}
                    <GlassCard className="p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-sm font-medium flex items-center gap-2">
                                <CreditCard size={14} className="text-blue-400" />
                                Payment Methods
                            </h3>
                            <button
                                onClick={() => {
                                    // In production, this would open Stripe checkout or payment form
                                    alert("Payment method integration requires Stripe setup. In production, this will open a secure payment form.");
                                }}
                                className="text-xs px-3 py-1.5 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg flex items-center gap-1"
                            >
                                <Plus size={12} /> Add Card
                            </button>
                        </div>

                        {paymentMethods.length === 0 ? (
                            <div className="text-center py-6">
                                <CreditCard size={32} className="mx-auto text-gray-600 mb-2" />
                                <p className="text-sm text-gray-500">No payment methods added</p>
                                <p className="text-xs text-gray-600 mt-1">Add a card to subscribe to paid plans</p>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                {paymentMethods.map((method) => (
                                    <div
                                        key={method.id}
                                        className="p-3 rounded-lg bg-white/5 flex items-center gap-3"
                                    >
                                        <CreditCard size={20} className="text-gray-400" />
                                        <div className="flex-1">
                                            <p className="text-sm font-medium capitalize">
                                                {method.card_brand} •••• {method.card_last4}
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                Expires {method.card_exp_month}/{method.card_exp_year}
                                            </p>
                                        </div>
                                        {method.is_default && (
                                            <span className="text-[10px] px-2 py-0.5 bg-blue-500/10 text-blue-400 rounded">
                                                Default
                                            </span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </GlassCard>

                    {/* Invoices */}
                    <GlassCard className="p-6">
                        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                            <Receipt size={14} className="text-amber-400" />
                            Recent Invoices
                        </h3>

                        {invoices.length === 0 ? (
                            <p className="text-sm text-gray-500 text-center py-4">No invoices yet</p>
                        ) : (
                            <div className="space-y-2">
                                {invoices.slice(0, 5).map((invoice) => (
                                    <div
                                        key={invoice.id}
                                        className="p-3 rounded-lg bg-white/5 flex items-center gap-3"
                                    >
                                        <Receipt size={16} className="text-gray-400" />
                                        <div className="flex-1">
                                            <p className="text-sm">{invoice.invoice_number}</p>
                                            <p className="text-xs text-gray-500">
                                                {formatDate(invoice.invoice_date)}
                                            </p>
                                        </div>
                                        <p className="font-medium">{formatCurrency(invoice.total)}</p>
                                        <span className={cn(
                                            "text-[10px] px-2 py-0.5 rounded",
                                            invoice.status === "paid"
                                                ? "bg-emerald-500/10 text-emerald-400"
                                                : "bg-amber-500/10 text-amber-400"
                                        )}>
                                            {invoice.status}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </GlassCard>
                </div>
            </div>
        </div>
    );
}
