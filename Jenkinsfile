// Jenkinsfile
pipeline {
    agent any

    stages {
        stage('Code Analysis') {
            steps {
                // Add execute permissions to the script
                sh 'chmod +x scripts/run_code_analyzer.sh'
                // Then, execute the script.
                // This script is responsible for generating 'code_quality_report.json' and 'some2.json'
                sh 'scripts/run_code_analyzer.sh'
            }
        }

        stage('Combine Build Info and Analysis Results') {
            steps {
                script {
                    // 1. Get Jenkins build details
                    def gitUrl = env.GIT_URL ?: ''
                    def repoName = gitUrl.tokenize('/').last().replace('.git', '')
                    def buildId = env.BUILD_ID
                    def buildNumber = env.BUILD_NUMBER

                    // Get build start time in milliseconds
                    def buildStartTimeMillis = currentBuild.startTimeInMillis
                    // Convert to a readable date/time string (e.g., "2025-06-06 19:30:00")
                    def buildStartTime = new Date(buildStartTimeMillis).format("yyyy-MM-dd HH:mm:ss")

                    // Initialize a flag to track JSON file reading success
                    def jsonFilesFoundSuccessfully = true

                    // 2. Read content from existing JSON files
                    def codeQualityData = [:] // Initialize as empty map
                    def issueReportData = [:]     // Initialize as empty map

                    try {
                        // Read code_quality_report.json (assuming it's in the workspace root)
                        codeQualityData = readJSON(file: 'code_quality_report.json')
                        echo "Successfully read code_quality_report.json"
                    } catch (FileNotFoundException e) {
                        echo "WARNING: code_quality_report.json NOT FOUND. Code quality data will be empty."
                        jsonFilesFoundSuccessfully = false // Mark failure if this file is missing
                    } catch (Exception e) { // Catch other potential parsing errors for robustness
                        echo "ERROR: Could not read or parse code_quality_report.json: ${e.message}"
                        jsonFilesFoundSuccessfully = false
                    }

                    try {
                        // Read some2.json (assuming it's in the workspace root)
                        issueReportData = readJSON(file: 'some2.json')
                        echo "Successfully read some2.json"
                    } catch (FileNotFoundException e) {
                        echo "WARNING: some2.json NOT FOUND. Issue report data will be empty."
                        jsonFilesFoundSuccessfully = false // Mark failure if this file is missing
                    } catch (Exception e) { // Catch other potential parsing errors for robustness
                        echo "ERROR: Could not read or parse some2.json: ${e.message}"
                        jsonFilesFoundSuccessfully = false
                    }

                    // Determine the combined result based on the JSON files found and overall Jenkins build status
                    def finalReportStatus
                    if (jsonFilesFoundSuccessfully && currentBuild.result == 'SUCCESS') {
                        finalReportStatus = 'success'
                    } else {
                        finalReportStatus = 'failure'
                    }

                    // 3. Create the combined JSON structure as a Groovy Map
                    def combinedJson = [
                        "repository_name": repoName,
                        "build_id": buildId,
                        "build_number": buildNumber,
                        "build_start_time": buildStartTime, // Added build start time
                        "final_status": finalReportStatus,  // Custom status based on JSON file presence
                        "issue_report": issueReportData,            // Content from some2.json
                        "code_quality": codeQualityData     // Content from code_quality_report.json
                    ]

                    // Define the output file path
                    def outputJsonFile = "combined_build_report.json"

                    // 4. Write the combined data to a new JSON file
                    writeJSON(file: outputJsonFile, json: combinedJson, pretty: 4)

                    echo "Combined build report written to ${outputJsonFile}"
                    // Optionally, print the content to the console for verification
                    sh "cat ${outputJsonFile}"
                }
            }
        }

        stage('Archive Report') {
            steps {
                // Archive the generated JSON report as a build artifact for easy access
                archiveArtifacts artifacts: 'combined_build_report.json', fingerprint: true
            }
        }

        stage('Post Combined Report') {
            steps {
                script {
                    // Read the JSON file content as a string
                    def jsonReportContent = readFile(file: 'combined_build_report.json')

                    // Define your API endpoint URL
                    // !!! IMPORTANT: Replace "YOUR_API_ENDPOINT_URL_HERE" with your actual API endpoint !!!
                    def apiEndpoint = "YOUR_API_ENDPOINT_URL_HERE"

                    echo "Attempting to POST combined report to: ${apiEndpoint}"

                    try {
                        // Use the httpRequest step to send the POST request
                        def response = httpRequest(
                            httpMode: 'POST',
                            url: apiEndpoint,
                            contentType: 'APPLICATION_JSON',
                            requestBody: jsonReportContent,
                            // Uncomment and configure 'customHeaders' if your API requires authentication (e.g., Bearer Token)
                            // customHeaders: [[name: 'Authorization', value: 'Bearer YOUR_TOKEN_HERE']],
                            // Or use basic authentication if needed (less secure than credentials if hardcoded)
                            // authentication: 'username:password', // Use withCredentials for sensitive info
                            // Optionally, specify which response codes are considered successful (2xx range is common)
                            validResponseCodes: '200:299'
                        )

                        echo "POST request completed. Status: ${response.status}"
                        echo "Response body: ${response.content}"

                        // Check if the POST request was successful based on the HTTP status code
                        if (response.status >= 200 && response.status < 300) {
                            echo "Report successfully sent to API."
                        } else {
                            // Fail the pipeline stage if the API returns an error status
                            error "Failed to send report. Status: ${response.status}, Message: ${response.content}"
                        }
                    } catch (Exception e) {
                        // Catch any network errors or exceptions during the HTTP request
                        error "Error during POST request: ${e.message}"
                    }
                }
            }
        }
    }
}