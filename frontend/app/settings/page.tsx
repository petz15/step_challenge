"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, ConversionRule } from "@/lib/api";
import Nav from "@/components/Nav";

export default function SettingsPage() {
  const { user, loading, refreshUser } = useAuth();
  const router = useRouter();
  const [rules, setRules] = useState<ConversionRule[]>([]);
  const [editedRules, setEditedRules] = useState<Record<string, { per_minute: string; per_km: string }>>({});
  const [name, setName] = useState("");
  const [weeklyGoal, setWeeklyGoal] = useState("");
  const [monthlyGoal, setMonthlyGoal] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingRule, setSavingRule] = useState<string | null>(null);
  const [profileMsg, setProfileMsg] = useState("");
  const [ruleMsg, setRuleMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) router.replace("/");
  }, [user, loading, router]);

  useEffect(() => {
    if (!user) return;
    setName(user.name);
    setWeeklyGoal(user.weekly_goal?.toString() ?? "");
    setMonthlyGoal(user.monthly_goal?.toString() ?? "");
    api.getConversionRules().then((r) => {
      setRules(r);
      const init: Record<string, { per_minute: string; per_km: string }> = {};
      r.forEach((rule) => {
        init[rule.activity_type] = {
          per_minute: rule.conversion_per_minute.toString(),
          per_km: rule.conversion_per_km.toString(),
        };
      });
      setEditedRules(init);
    });
  }, [user]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileMsg("");
    try {
      await api.updateUserSettings({
        name: name || undefined,
        weekly_goal: weeklyGoal ? Number(weeklyGoal) : null,
        monthly_goal: monthlyGoal ? Number(monthlyGoal) : null,
      });
      await refreshUser();
      setProfileMsg("Saved!");
    } catch {
      setProfileMsg("Failed to save");
    } finally {
      setSavingProfile(false);
    }
  };

  const handleSaveRule = async (activityType: string) => {
    setSavingRule(activityType);
    setRuleMsg(null);
    const edited = editedRules[activityType];
    if (!edited) return;
    try {
      const res = await api.updateConversionRule(activityType, {
        conversion_per_minute: Number(edited.per_minute),
        conversion_per_km: Number(edited.per_km),
      });
      setRuleMsg(res.message);
    } catch {
      setRuleMsg("Failed to update rule");
    } finally {
      setSavingRule(null);
    }
  };

  if (loading || !user) return null;

  return (
    <div className="min-h-screen">
      <Nav />
      <main className="max-w-2xl mx-auto px-4 py-6 space-y-8">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

        {/* Profile */}
        <section className="bg-white rounded-2xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Profile & Goals</h2>
          <form onSubmit={handleSaveProfile} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Weekly Goal (steps)</label>
                <input
                  type="number"
                  min="0"
                  value={weeklyGoal}
                  onChange={(e) => setWeeklyGoal(e.target.value)}
                  placeholder="e.g. 70000"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Goal (steps)</label>
                <input
                  type="number"
                  min="0"
                  value={monthlyGoal}
                  onChange={(e) => setMonthlyGoal(e.target.value)}
                  placeholder="e.g. 280000"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={savingProfile}
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                {savingProfile ? "Saving…" : "Save Profile"}
              </button>
              {profileMsg && <span className="text-sm text-green-600">{profileMsg}</span>}
            </div>
          </form>
        </section>

        {/* Conversion Rules */}
        <section className="bg-white rounded-2xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Conversion Rules</h2>
          <p className="text-sm text-gray-500 mb-4">
            Changing a rule retroactively recalculates all matching activities.
          </p>
          {ruleMsg && (
            <p className="text-sm text-green-600 mb-3">{ruleMsg}</p>
          )}
          <div className="space-y-3">
            {rules.map((rule) => {
              const edited = editedRules[rule.activity_type] ?? {
                per_minute: rule.conversion_per_minute.toString(),
                per_km: rule.conversion_per_km.toString(),
              };
              return (
                <div key={rule.activity_type} className="flex items-center gap-3 py-2 border-b border-gray-100 last:border-0">
                  <span className="text-sm font-medium text-gray-700 w-32 shrink-0">{rule.activity_type}</span>
                  <div className="flex items-center gap-2 flex-1">
                    <label className="text-xs text-gray-500 shrink-0">per min</label>
                    <input
                      type="number"
                      min="0"
                      step="0.1"
                      value={edited.per_minute}
                      onChange={(e) =>
                        setEditedRules((prev) => ({
                          ...prev,
                          [rule.activity_type]: { ...edited, per_minute: e.target.value },
                        }))
                      }
                      className="w-20 border border-gray-300 rounded px-2 py-1 text-sm text-center focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                    <label className="text-xs text-gray-500 shrink-0">per km</label>
                    <input
                      type="number"
                      min="0"
                      step="1"
                      value={edited.per_km}
                      onChange={(e) =>
                        setEditedRules((prev) => ({
                          ...prev,
                          [rule.activity_type]: { ...edited, per_km: e.target.value },
                        }))
                      }
                      className="w-20 border border-gray-300 rounded px-2 py-1 text-sm text-center focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                  <button
                    onClick={() => handleSaveRule(rule.activity_type)}
                    disabled={savingRule === rule.activity_type}
                    className="text-xs bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-lg hover:bg-indigo-100 disabled:opacity-50 transition-colors shrink-0"
                  >
                    {savingRule === rule.activity_type ? "Saving…" : "Save"}
                  </button>
                </div>
              );
            })}
          </div>
        </section>
      </main>
    </div>
  );
}
