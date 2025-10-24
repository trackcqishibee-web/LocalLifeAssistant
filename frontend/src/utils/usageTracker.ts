/**
 * Usage tracking utilities for anonymous user trial limits
 */

const USAGE_KEY = 'user_usage_stats';

export interface UsageStats {
  anonymous_user_id: string;
  interaction_count: number;
  trial_remaining: number;
  is_registered: boolean;
  registration_prompted: boolean;
}

export function getUsageStats(): UsageStats | null {
  const data = localStorage.getItem(USAGE_KEY);
  return data ? JSON.parse(data) : null;
}

export function updateUsageStats(stats: Partial<UsageStats>): void {
  const current = getUsageStats() || {
    anonymous_user_id: '',
    interaction_count: 0,
    trial_remaining: 10,
    is_registered: false,
    registration_prompted: false
  };
  
  const updated = { ...current, ...stats };
  localStorage.setItem(USAGE_KEY, JSON.stringify(updated));
}

export function shouldShowRegistrationPrompt(): boolean {
  const stats = getUsageStats();
  if (!stats) return false;
  
  return stats.trial_remaining <= 3 && !stats.is_registered && !stats.registration_prompted;
}

export function markRegistrationPrompted(): void {
  updateUsageStats({ registration_prompted: true });
}

export function getTrialWarningMessage(remaining: number): string {
  if (remaining === 0) {
    return "⚠️ Trial expired! Please register to continue.";
  } else if (remaining <= 3) {
    return `⚠️ ${remaining} free interactions remaining. Register to keep your history!`;
  }
  return "";
}

export function clearUsageStats(): void {
  localStorage.removeItem(USAGE_KEY);
}
