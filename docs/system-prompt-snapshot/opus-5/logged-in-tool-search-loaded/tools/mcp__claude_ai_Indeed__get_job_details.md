# mcp__claude_ai_Indeed__get_job_details

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Get detailed descriptions of a job on Indeed.

This provides comprehensive information about a specific job including
title, company, location, salary, job description, and application
links.
The job is sourced from Indeed's job search API.

**Rules:**
1. The result includes a link to apply for the job. It is very
   important
   to embed the apply link to the job title so the user can click
   the job
   title to apply for the job.
2. Keep URLs intact - don't strip parameters.

Returns:
    Formatted job details as markdown

## input_schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "job_id": {
      "description": "The job ID to get details for. This field is required.",
      "type": "string"
    }
  },
  "required": [
    "job_id"
  ]
}
```
