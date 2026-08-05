export type MetricDirection = 'increase' | 'decrease';

export type MetricType =
  | 'weight'
  | 'distance'
  | 'duration'
  | 'repetitions'
  | 'working_weight'
  | 'training_volume'
  | 'steps'
  | 'resting_heart_rate'
  | 'sleep_hours';

export type GoalStatus = 'active' | 'completed' | 'paused';

export interface Goal {
  id: string;
  title: string;
  metricType: MetricType;
  direction: MetricDirection;
  startValue: number;
  targetValue: number;
  currentValue: number;
  unit: string;
  targetDate?: string;
  status: GoalStatus;
  createdAt: string;
  updatedAt: string;
}

export interface MetricEntry {
  id: string;
  goalId: string;
  date: string;
  metricType: MetricType;
  value: number;
  unit: string;
  comment?: string;
  source: 'manual' | 'mock_device';
}

export interface ForecastResult {
  goalId: string;
  dataPoints: number;
  weeklyRate: number | null;
  remainingValue: number;
  estimatedWeeks: number | null;
  estimatedDate: string | null;
  confidence: 'low' | 'medium' | 'high';
  trend: 'toward_goal' | 'away_from_goal' | 'stable' | 'insufficient_data';
  explanation: string;
}

export interface HealthProfile {
  allergies: string[];
  injuries: string[];
  diagnoses: string[];
  medications: string[];
  doctorRestrictions: string[];
  familyHistory: string[];
  demoOnly: true;
}

export type DeviceMetric =
  | 'steps'
  | 'heart_rate'
  | 'resting_heart_rate'
  | 'sleep'
  | 'distance'
  | 'calories'
  | 'spo2'
  | 'stress';

export interface DeviceSample {
  id: string;
  provider: string;
  metric: DeviceMetric;
  value: number;
  unit: string;
  recordedAt: string;
  synthetic: true;
}

export type ContextEventType =
  | 'goal_progress'
  | 'step_goal_reached'
  | 'sleep_low'
  | 'heart_rate_high'
  | 'workout_completed'
  | 'location_food'
  | 'location_park'
  | 'dog_walk_due';

export interface ContextEvent {
  id: string;
  type: ContextEventType;
  timestamp: string;
  source: string;
  data: Record<string, unknown>;
  synthetic: true;
}

export interface AIRecommendation {
  title: string;
  message: string;
  reasons: string[];
  suggestedActions: string[];
  safetyLevel: 'green' | 'yellow' | 'red';
  disclaimer?: string;
}

export type SubscriptionTier = 'free' | 'pro';
