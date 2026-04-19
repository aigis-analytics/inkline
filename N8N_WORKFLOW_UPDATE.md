# n8n Workflow Update for Visual Direction Agent

## Current State
`inkblot-icon-generator-workflow.json` is a hardcoded Gemini icon generator.

## Required Changes

### 1. Webhook Node
- Already accepts POST to `/inkblot-icon` 
- Body should now contain: `{"prompt": "...", "style": "..."}`

### 2. Gemini API Node (HTTP Request)
**Change from:** Hardcoded prompt in bodyParametersUiExpression  
**Change to:** Dynamic prompt from webhook body

Replace the hardcoded `contents` value:
```json
"value": "[{\"parts\":[{\"text\":\"{{ $json.body.prompt }}\"}]}]"
```

### 3. Response Node (NEW)
- Remove the "Write Binary File" node
- Add HTTP Response node after Gemini API
- Return JSON:
```json
{
  "image_path": "{{ returned file path from Gemini }}"
}
```

OR modify the Write Binary File to:
1. Save image with timestamp: `/tmp/inkline_bg_{{ Date.now() }}.png`
2. Add HTTP Response node to return `{"image_path": "/tmp/inkline_bg_<timestamp>.png"}`

## Quick Fix (Minimal Change)
Keep Write Binary File node, add HTTP Response that reads:
```
{
  "image_path": "${{ $node['write_file'].json.file_path }}"
}
```

## Testing
After updating workflow:
1. POST to n8n with: `{"prompt": "test background image"}`
2. Verify response: `{"image_path": "/path/to/image.png"}`
3. VDA will call this workflow with background requests from VisualBrief
