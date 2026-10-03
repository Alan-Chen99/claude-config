# mcp__claude_ai_Indeed__search_jobs

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Search for jobs on Indeed. These jobs are sourced from Indeed's job search API.

**Rules:**
1. The result includes links to apply for each job. It is very important to embed the apply link to EACH job title so the user can click the job titles to apply for the jobs.
2. Keep URLs intact - don't strip parameters.

Returns:
    Formatted job search results as markdown

## input_schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "search": {
      "description": "The job title or keywords to search for",
      "type": "string"
    },
    "location": {
      "description": "City and state location for search or \"remote\" to search for remote positions",
      "type": "string"
    },
    "country_code": {
      "description": "An ISO 3166 two letter country code (e.g., 'US', 'CA'). Pull from a previous value if already provided by the user.",
      "type": "string"
    },
    "job_type": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "One of 'fulltime', 'parttime', 'contract', 'internship', 'temporary' (optional)"
    }
  },
  "required": [
    "search",
    "location",
    "country_code"
  ]
}
```
