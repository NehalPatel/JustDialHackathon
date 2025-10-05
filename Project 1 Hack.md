# Project 1 Hack — Auto-Moderation Plugin for Video Content

## Project Goal

Create a plugin that automatically evaluates user-uploaded video media for violations of platform policies (nudity, copyright, fraud, inappropriate content requiring blur, etc.) and allows only moderated, compliant content to go live.

## Core Functionality & Output

### 1. Input

- Video File: Accept video files in common formats (e.g., MP4, MOV, AVI, WMV).
- Plugin Configuration: Support configurations defining sensitivity levels for each type of check (e.g., strict/moderate/lenient for nudity detection) and acceptable thresholds for copyright infringement.
- Watermark Overlay: Receive platform watermark to identify the platform ownership of a video.

### 2. Processing & Analysis

The plugin must perform the following checks on uploaded videos:

#### Nudity Detection

- Output: Score or confidence level indicating presence and degree of nudity.
- Categorization: Differentiate types of nudity (e.g., partial, full, suggestive).
- Timestamping: Identify specific timestamps where nudity is detected.

#### Copyright Infringement Detection

- Output: Score or percentage indicating likelihood of copyright infringement.
- Source Identification (Ideal): Identify potential sources (e.g., song titles, movie clips), if possible.
- Timestamping: Mark timestamps where potentially infringing content appears.

#### Fraud Detection (Content-Based)

- Output: Score indicating likelihood of fraudulent activity based on video content.
- Guidance: Define specific fraud types.
- Examples: Spammy links, misleading promotions, fake giveaways.

#### Blur Detection (For Inappropriate Content)

- Output: Identify timestamps and regions within the video that require blurring.
- Categorization: Reasons for blur (e.g., violence, offensive gestures, personally identifiable information).

### 3. Auto-Moderation Decision

- Output: Clear "Approve" or "Reject" decision based on analysis results and configured sensitivity levels.
- Reasoning: Provide explanation for the decision. For example:
  - "Rejected: Nudity detected at 0:15–0:20 exceeding the 'moderate' sensitivity threshold."
  - "Approved: All checks passed."
- Actionable Data: If rejected, include specific data points (timestamps, scores, categories) that triggered the rejection, to assist admin review.

### 4. Reporting & Logging

- Detailed Logs: Record all analysis results, decisions, and reasoning for each video processed.
- Reporting Dashboard (Optional): Display key metrics such as:
  - Total videos processed
  - Approval/Rejection rates
  - Breakdown of rejection reasons
  - Performance metrics of ML models (e.g., false positive and false negative rates)
- Alerts: Configure alerts for specific events (e.g., sudden spike in rejections for a particular reason).

## Technical Requirements

1. API Interface: Expose a well-defined API for integration with the platform. The API should allow:
   - Uploading videos for analysis
   - Retrieving analysis results and moderation decisions
   - Configuring plugin settings
2. Scalability: Design to handle a high volume of concurrent video uploads.
3. Performance: Ensure reasonably fast analysis to avoid publishing delays; define acceptable processing times.
4. Security: Protect user data and secure the plugin.
5. ML Model Updates: Provide a mechanism for updating underlying ML models to improve accuracy and adapt to evolving content trends.

## Success Metrics

- Accuracy: High accuracy in detecting policy violations (low false positive and false negative rates). Define acceptable error rates.
- Efficiency: Fast processing times.
- Scalability: Ability to handle a large volume of video uploads.
- Reduced Manual Moderation: Significant reduction in required manual moderation.

## Example Workflow

1. User uploads a video.
2. Platform sends the video to the plugin via the API.
3. Plugin analyzes the video for nudity, copyright infringement, fraud, etc.
4. Plugin generates a moderation decision (Approve/Reject) and a detailed report.
5. Platform receives the decision.
6. If approved, the video is published.
7. If rejected, the video is not published, and the platform displays the rejection reason (if possible) or notifies administrators for review.