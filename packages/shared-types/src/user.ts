/**
 * User types for the Keiko user service.
 */

export type UserRole = 'user' | 'admin' | 'moderator';

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  role: UserRole;
  department?: string;
  created_at: string;
  updated_at: string;
}

export interface UserPreferences {
  language: 'en' | 'de';
  theme: 'light' | 'dark' | 'system';
  notifications_enabled: boolean;
  email_notifications: boolean;
  default_model?: string;
  default_temperature?: number;
}

export interface UserSettings {
  profile: UserProfile;
  preferences: UserPreferences;
}

export interface UpdateProfileRequest {
  name?: string;
  avatar_url?: string;
  department?: string;
}

export interface UpdatePreferencesRequest {
  language?: 'en' | 'de';
  theme?: 'light' | 'dark' | 'system';
  notifications_enabled?: boolean;
  email_notifications?: boolean;
  default_model?: string;
  default_temperature?: number;
}

