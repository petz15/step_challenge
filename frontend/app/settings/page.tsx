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
  const [editedRules, setEditedRules] = useState<Record<string, { per_minute: string; per_km: string; multiplier: string }>>({});
  const [name, setName] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingRule, setSavingRule] = useState<string | null>(null);
  const [savingAll, setSavingAll] = useState(false);
  const [profileMsg, setProfileMsg] = useState("");
  const [ruleMsg, setRuleMsg] = useState<string | null>(null);
  const [newName, setNewName] = useState("");
  const [newPerMin, setNewPerMin] = useState("");
  const [newPerKm, setNewPerKm] = useState("");
  const [addingRule, setAddingRule] = useState(false);
  const [addMsg, setAddMsg] = useState("");

  // Garmin state
  const [garminConnected, setGarminConnected] = useState(false);
  const [garminEmail, setGarminEmail] = useState<string | null>(null);
  const [garminFormEmail, setGarminFormEmail] = useState("");
  const [garminFormPassword, setGarminFormPassword] = useState("");
  const [garminConnecting, setGarminConnecting] = useState(false);
  const [garminMsg, setGarminMsg] = useState("");
  const [garminSyncing, setGarminSyncing] = useState(false);
  const [garminSyncMsg, setGarminSyncMsg] = useState("");
  const [garminSyncStart, setGarminSyncStart] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 7);
    return d.toISOString().slice(0, 10);
  });
  const [garminSyncEnd] = useState(new Date().toISOString().slice(0, 10));

  useEffect(() => {
    if (!loading && !user) router.replace("/");
  }, [user, loading, router]);

  useEffect(() => {
    if (!user) return;
    setName(user.name);
    if (user.is_superuser) {
      api.getConversionRules().then((r) => {
        setRules(r);
        const init: Record<string, { per_minute: string; per_km: string; multiplier: string }> = {};
        r.forEach((rule) => {
          init[rule.activity_type] = {
            per_minute: rule.conversion_per_minute.toString(),
            per_km: rule.conversion_per_km.toString(),
            multiplier: rule.step_multiplier.toString(),
          };
        });
        setEditedRules(init);
      });
    }
    api.garminStatus().then((s) => {
      setGarminConnected(s.connected);
      setGarminEmail(s.email);
    }).catch(() => {});
  }, [user]);

  const handleGarminConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setGarminConnecting(true);
    setGarminMsg("");
    try {
      const res = await api.garminConnect(garminFormEmail.trim(), garminFormPassword);
      setGarminConnected(res.connected);
      setGarminEmail(res.email);
      setGarminFormPassword("");
      setGarminMsg("Connected to Garmin Connect!");
    } catch (err: unknown) {
      setGarminMsg(err instanceof Error ? err.message : "Failed to connect");
    } finally {
      setGarminConnecting(false);
    }
  };

  const handleGarminDisconnect = async () => {
    await api.garminDisconnect();
    setGarminConnected(false);
    setGarminEmail(null);
    setGarminMsg("Disconnected from Garmin.");
  };

  const handleGarminSync = async () => {
    setGarminSyncing(true);
    setGarminSyncMsg("");
    try {
      const res = await api.garminSync(garminSyncStart, garminSyncEnd);
      const warn = res.warnings?.length ? ` Warning: ${res.warnings.join('; ')}` : '';
      setGarminSyncMsg(
        `Done — ${res.imported} imported, ${res.steps_updated} day totals updated, ${res.skipped} skipped.${warn}`
      );
    } catch (err: unknown) {
      setGarminSyncMsg(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setGarminSyncing(false);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileMsg("");
    try {
      await api.updateUserSettings({ name: name || undefined });
      await refreshUser();
      setProfileMsg("Saved!");
    } catch {
      setProfileMsg("Failed to save");
    } finally {
      setSavingProfile(false);
    }
  };

  const suggestMultipliers = () => {
    const baseline = rules.find((r) => r.activity_type === "Walking, Moderate");
    const baseRate = baseline ? baseline.conversion_per_minute : null;
    if (!baseRate || baseRate <= 0) return;
    setEditedRules((prev) => {
      const next = { ...prev };
      rules.forEach((rule) => {
        if (rule.conversion_per_minute > 0) {
          const suggested = Math.round((rule.conversion_per_minute / baseRate) * 100) / 100;
          next[rule.activity_type] = {
            ...(next[rule.activity_type] ?? {
              per_minute: rule.conversion_per_minute.toString(),
              per_km: rule.conversion_per_km.toString(),
            }),
            multiplier: suggested.toString(),
          };
        }
      });
      return next;
    });
  };

  const handleAddRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setAddingRule(true);
    setAddMsg("");
    try {
      const rule = await api.createConversionRule({
        activity_type: newName.trim(),
        conversion_per_minute: Number(newPerMin) || 0,
        conversion_per_km: Number(newPerKm) || 0,
        step_multiplier: 1.0,
      });
      setRules((prev) => [...prev, rule].sort((a, b) => a.activity_type.localeCompare(b.activity_type)));
      setEditedRules((prev) => ({
        ...prev,
        [rule.activity_type]: {
          per_minute: rule.conversion_per_minute.toString(),
          per_km: rule.conversion_per_km.toString(),
          multiplier: rule.step_multiplier.toString(),
        },
      }));
      setNewName("");
      setNewPerMin("");
      setNewPerKm("");
      setAddMsg(`"${rule.activity_type}" added.`);
    } catch (err: unknown) {
      setAddMsg(err instanceof Error ? err.message : "Failed to add");
    } finally {
      setAddingRule(false);
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
        step_multiplier: Number(edited.multiplier),
      });
      setRuleMsg(res.message);
    } catch {
      setRuleMsg("Failed to update rule");
    } finally {
      setSavingRule(null);
    }
  };

  const handleSaveAll = async () => {
    setSavingAll(true);
    setRuleMsg(null);
    try {
      await Promise.all(
        rules.map((rule) => {
          const edited = editedRules[rule.activity_type];
          if (!edited) return Promise.resolve();
          return api.updateConversionRule(rule.activity_type, {
            conversion_per_minute: Number(edited.per_minute),
            conversion_per_km: Number(edited.per_km),
            step_multiplier: Number(edited.multiplier),
          });
        })
      );
      setRuleMsg(`All ${rules.length} rules saved and activities recalculated.`);
    } catch {
      setRuleMsg("Failed to save some rules.");
    } finally {
      setSavingAll(false);
    }
  };

  if (loading || !user) return null;

  return (
    <div className="min-h-screen">
      <Nav />
      <main className="max-w-2xl mx-auto px-4 py-6 pb-24 space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

        {/* Profile */}
        <section className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Profile</h2>
          <form onSubmit={handleSaveProfile} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={savingProfile}
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                {savingProfile ? "Saving…" : "Save"}
              </button>
              {profileMsg && <span className="text-sm text-green-600">{profileMsg}</span>}
            </div>
          </form>
        </section>

        {/* Garmin Sync */}
        <section className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Garmin Sync</h2>
          <p className="text-sm text-gray-500 mb-4">
            Import activities directly from Garmin Connect. Duplicates are skipped automatically.
            If your account has 2-factor authentication enabled, disable it on Garmin Connect first.
          </p>

          {garminConnected ? (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm">
                <span className="w-2 h-2 rounded-full bg-green-500 shrink-0" />
                <span className="text-gray-700">Connected as <strong>{garminEmail}</strong></span>
                <button
                  onClick={handleGarminDisconnect}
                  className="ml-auto text-xs text-red-500 hover:text-red-700 hover:underline"
                >
                  Disconnect
                </button>
              </div>

              <div className="flex gap-3 items-end flex-wrap">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">From</label>
                  <input
                    type="date"
                    value={garminSyncStart}
                    onChange={(e) => setGarminSyncStart(e.target.value)}
                    className="border border-gray-300 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">To</label>
                  <input
                    type="date"
                    value={garminSyncEnd}
                    disabled
                    className="border border-gray-200 rounded-lg px-2 py-1.5 text-sm bg-gray-50 text-gray-500"
                  />
                </div>
                <button
                  onClick={handleGarminSync}
                  disabled={garminSyncing}
                  className="bg-indigo-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                >
                  {garminSyncing ? "Syncing…" : "Sync Activities"}
                </button>
              </div>
              {garminSyncMsg && (
                <p className={`text-sm ${garminSyncMsg.includes("failed") || garminSyncMsg.includes("Failed") ? "text-red-600" : "text-green-600"}`}>
                  {garminSyncMsg}
                </p>
              )}
            </div>
          ) : (
            <form onSubmit={handleGarminConnect} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Garmin Connect Email</label>
                  <input
                    type="email"
                    value={garminFormEmail}
                    onChange={(e) => setGarminFormEmail(e.target.value)}
                    required
                    placeholder="you@example.com"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                  <input
                    type="password"
                    value={garminFormPassword}
                    onChange={(e) => setGarminFormPassword(e.target.value)}
                    required
                    placeholder="••••••••"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button
                  type="submit"
                  disabled={garminConnecting}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                >
                  {garminConnecting ? "Connecting…" : "Connect Garmin"}
                </button>
                {garminMsg && (
                  <span className={`text-sm ${garminMsg.includes("Connected") ? "text-green-600" : "text-red-600"}`}>
                    {garminMsg}
                  </span>
                )}
              </div>
            </form>
          )}
        </section>

        {/* Conversion Rules — superuser only */}
        {user.is_superuser && <section className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-start justify-between mb-1">
            <h2 className="text-lg font-semibold text-gray-900">Conversion Rules</h2>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={suggestMultipliers}
                className="text-xs text-gray-500 hover:text-gray-700 underline-offset-2 hover:underline"
              >
                Suggest multipliers
              </button>
              <button
                type="button"
                onClick={handleSaveAll}
                disabled={savingAll}
                className="text-xs bg-indigo-600 text-white px-3 py-1.5 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                {savingAll ? "Saving…" : "Save All"}
              </button>
            </div>
          </div>
          <p className="text-sm text-gray-500 mb-4">
            Changing a rule retroactively recalculates all matching activities. The <strong>step ×</strong> multiplier weights real step counts (running, walking) from Garmin — e.g. set running to 2.0 so each running step counts double.
          </p>

          {/* Add custom activity */}
          <form onSubmit={handleAddRule} className="flex gap-2 items-end mb-5 pb-5 border-b border-gray-100">
            <div className="flex-1">
              <label className="block text-xs text-gray-500 mb-1">New activity name</label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="e.g. Paddleboarding"
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div className="w-20">
              <label className="block text-xs text-gray-500 mb-1">per min</label>
              <input
                type="number" min="0" step="0.1" value={newPerMin}
                onChange={(e) => setNewPerMin(e.target.value)}
                placeholder="0"
                className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-sm text-center focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div className="w-20">
              <label className="block text-xs text-gray-500 mb-1">per km</label>
              <input
                type="number" min="0" step="1" value={newPerKm}
                onChange={(e) => setNewPerKm(e.target.value)}
                placeholder="0"
                className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-sm text-center focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <button
              type="submit"
              disabled={addingRule || !newName.trim()}
              className="bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors shrink-0"
            >
              {addingRule ? "Adding…" : "Add"}
            </button>
          </form>
          {addMsg && <p className="text-sm text-green-600 mb-3">{addMsg}</p>}
          {ruleMsg && (
            <p className="text-sm text-green-600 mb-3">{ruleMsg}</p>
          )}
          <div className="space-y-3">
            {rules.map((rule) => {
              const edited = editedRules[rule.activity_type] ?? {
                per_minute: rule.conversion_per_minute.toString(),
                per_km: rule.conversion_per_km.toString(),
                multiplier: rule.step_multiplier.toString(),
              };
              return (
                <div key={rule.activity_type} className="py-3 border-b border-gray-100 last:border-0">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">{rule.activity_type}</span>
                    <button
                      onClick={() => handleSaveRule(rule.activity_type)}
                      disabled={savingRule === rule.activity_type}
                      className="text-xs bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-lg hover:bg-indigo-100 disabled:opacity-50 transition-colors"
                    >
                      {savingRule === rule.activity_type ? "Saving…" : "Save"}
                    </button>
                  </div>
                  <div className="flex items-center gap-3 flex-wrap">
                    <div className="flex items-center gap-1">
                      <label className="text-xs text-gray-500 w-14 shrink-0">per min</label>
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
                        className="w-16 border border-gray-300 rounded px-2 py-1 text-sm text-center focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      />
                    </div>
                    <div className="flex items-center gap-1">
                      <label className="text-xs text-gray-500 w-10 shrink-0">per km</label>
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
                        className="w-16 border border-gray-300 rounded px-2 py-1 text-sm text-center focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      />
                    </div>
                    <div className="flex items-center gap-1">
                      <label className="text-xs text-gray-500 shrink-0">step ×</label>
                      <input
                        type="number"
                        min="0.1"
                        max="10"
                        step="0.05"
                        value={edited.multiplier}
                        onChange={(e) =>
                          setEditedRules((prev) => ({
                            ...prev,
                            [rule.activity_type]: { ...edited, multiplier: e.target.value },
                          }))
                        }
                        className="w-16 border border-gray-300 rounded px-2 py-1 text-sm text-center focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>}
      </main>
    </div>
  );
}
