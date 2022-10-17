/*
Copyright © 2022 Christopher Lawlor <lawlor.chris@gmail.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

	http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
package cmd

import (
	"fmt"

	"github.com/chrislawlor/scanli/scanners/pip"
	"github.com/spf13/cobra"
)

var pipFlag []string

// scanCmd represents the scan command
var scanCmd = &cobra.Command{
	Use:   "scan",
	Short: "Scan one or more dependency specification files.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Print(pip.Scan(pipFlag))

	},
}

func init() {
	scanCmd.Flags().StringArrayVarP(&pipFlag, "pip", "p", []string{}, "Scan pip requirements file")

	rootCmd.AddCommand(scanCmd)
}
