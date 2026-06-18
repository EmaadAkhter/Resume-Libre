export const EVENTS = {
  // Resume generation lifecycle
  GENERATION_STARTED: 'generation:started',
  GENERATION_TOKEN: 'generation:token',
  GENERATION_COMPLETED: 'generation:completed',
  GENERATION_FAILED: 'generation:failed',

  // Notifications (toasts)
  NOTIFICATION_SHOW: 'notification:show',
  NOTIFICATION_DISMISS: 'notification:dismiss',

  // Backend connection status
  BACKEND_CONNECTED: 'backend:connected',
  BACKEND_DISCONNECTED: 'backend:disconnected',

  // Export
  EXPORT_REQUESTED: 'export:requested',
  EXPORT_COMPLETED: 'export:completed',
  EXPORT_FAILED: 'export:failed',

  // File upload
  FILE_UPLOADED: 'file:uploaded',
  FILE_REMOVED: 'file:removed',

  // System prompt
  SYSTEM_PROMPT_UPDATED: 'system-prompt:updated',
  SYSTEM_PROMPT_RESET: 'system-prompt:reset',

  // Auth
  AUTH_LOGIN: 'auth:login',
  AUTH_LOGOUT: 'auth:logout',
  AUTH_REGISTER: 'auth:register',

  // Branches
  BRANCH_CREATED: 'branch:created',
  BRANCH_SWITCHED: 'branch:switched',
  BRANCH_MERGED: 'branch:merged',

  // Templates
  TEMPLATE_SELECTED: 'template:selected',
  TEMPLATE_UPLOADED: 'template:uploaded',
}
