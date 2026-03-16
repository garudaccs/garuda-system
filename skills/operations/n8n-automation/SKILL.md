# N8N Automation

## Metadata
- **ID:** n8n-automation
- **Version:** 1.0.0
- **Source:** garuda/internal
- **Agents:** lakshmi, hanuman
- **Tags:** n8n, automation, workflow, integration

## Purpose
N8N workflow automation patterns for Garuda operations.

## N8N Instance
- **URL:** Configured in credentials
- **Access:** Via Operations Lane

## Common Workflows

### 1. Google Drive Sync
```
Trigger: Schedule (daily)
-> Google Drive: List files
-> Filter: New files
-> Process: Download/Transform
-> Action: Save to project
```

### 2. Email Notifications
```
Trigger: Webhook
-> Validate: Check source
-> Template: Generate email
-> Brevo: Send email
-> Log: Record sent
```

### 3. Social Media Posting
```
Trigger: Schedule
-> Content: Get from queue
-> Pabbly: Post to platforms
-> Update: Mark as posted
```

## Best Practices

1. **Error Handling**
- Always add error nodes
- Log failures to monitoring
- Set up retry logic

2. **Security**
- Use credentials store
- Never hardcode secrets
- Validate webhooks

3. **Performance**
- Batch operations when possible
- Use schedules wisely
- Monitor execution time

## Integration Points
- **Brevo:** Email campaigns
- **Google Drive:** File storage
- **Pabbly:** Social media
- **GitHub:** Repository updates

## Workflow Naming
`[LANE] - [ACTION] - [FREQUENCY]`
Example: `MARKETING - Social Post - Daily`
