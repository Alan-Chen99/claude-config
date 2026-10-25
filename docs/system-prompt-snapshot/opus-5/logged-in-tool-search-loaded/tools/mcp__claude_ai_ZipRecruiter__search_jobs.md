# mcp__claude_ai_ZipRecruiter__search_jobs

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Use this tool whenever the user asks to find, browse, view, recommend, or search for jobs, roles, openings, gigs, internships, or job listings. It only shows jobs that are within the United States or Canada.
Guidelines:
- Do not provide fields unless the user explicitly provides them.
- The tool provides the search results all in one list, so if the user intends to search for multiple job roles, it may be better to invoke the tool for each job role separately.
- If the user has not provided a location and is not asking for remote jobs, ask the user for a location before calling this tool. If you call without a location, results will default to a United States-wide search and the user will be warned.
- If a previous search_jobs response in this conversation included a conversation_id, echo that exact value back and never invent or modify it; omit it otherwise.
- Each result's listing_key is an internal identifier. Keep it for follow-up tool calls, but never show it to the user or mention it when describing the results.

Notes:
- When provided radius_miles, jobs will be included in the result if their location's boundaries approximately fall within radius miles of the requested location's boundaries.
- If a salary range is provided, a job will be included in the results if the job's salary range overlaps with the requested salary range.
- Returns up to 5 jobs per call.


## input_schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "conversation_id": {
      "description": "The conversation_id returned by a previous search_jobs result in this conversation to track requests within a single conversation.",
      "type": "string"
    },
    "job_role": {
      "description": "Specific job role to search for. This can be omitted if the user's intentions are to search broadly. Good example: 'software engineer', Bad example: 'sitting job'",
      "type": "string"
    },
    "skills": {
      "description": "Explicit skills mentioned by the user that are relevant to the job they're looking for.  Good example: 'SQL'",
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "location": {
      "description": "Concrete city, state, zip code, or address to search in. Good example: 'Montreal, Quebec', Bad example: 'near me'",
      "type": "string"
    },
    "radius_miles": {
      "description": "Search radius in miles from the location.",
      "type": "number"
    },
    "country_admin_code": {
      "description": "ISO-3166-1 alpha-2 country code. Only set this when a concrete location is provided and the country is known from that location. Must match the location that user wants to search in.",
      "type": "string"
    },
    "max_posted_minutes_ago": {
      "description": "Maximum number of minutes ago the job was posted. MIN: 1440",
      "type": "number",
      "minimum": 1440
    },
    "salary_min": {
      "description": "Minimum annual salary filter. MIN: 0",
      "type": "number",
      "minimum": 0,
      "maximum": 300000
    },
    "salary_max": {
      "description": "Maximum annual salary filter and must be greater than salary_min. MAX: 300000",
      "type": "number",
      "minimum": 0,
      "maximum": 300000
    },
    "location_types": {
      "description": "The location type of the job.",
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "LOCATION_TYPE_UNSPECIFIED",
          "PHYSICAL",
          "REMOTE",
          "HYBRID"
        ]
      }
    },
    "employment_types": {
      "description": "The employment type of the job.",
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "EMPLOYMENT_TYPE_UNSPECIFIED",
          "FULL_TIME",
          "PART_TIME",
          "CONTRACT",
          "CONTRACT_TO_HIRE",
          "TEMPORARY",
          "AS_NEEDED",
          "OTHER",
          "INTERNSHIP"
        ]
      }
    },
    "seniority_classes": {
      "description": "The seniority class of the job.",
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "SENIORITY_CLASS_UNSPECIFIED",
          "NO_EXPERIENCE",
          "JUNIOR",
          "MID",
          "SENIOR"
        ]
      }
    },
    "unsupported_filters": {
      "description": "Any unsupported filters provided by the user. Good examples: 401K, benefits",
      "type": "object",
      "propertyNames": {
        "type": "string"
      },
      "additionalProperties": {
        "type": "string"
      }
    },
    "offset": {
      "description": "Number of results to skip for pagination",
      "type": "number"
    }
  },
  "additionalProperties": false
}
```
