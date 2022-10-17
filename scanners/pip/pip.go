package pip

import (
	"bufio"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"regexp"
	"time"
)

type PyPiPackageMeta struct {
	Info Info
}

type Info struct {
	Author                   string
	Author_email             string
	Bugtrack_url             string
	Classifiers              []string
	Description              string
	Description_content_type string
	Docs_url                 string
	Download_url             string
	Home_page                string
	Keywords                 string
	License                  string
	Maintainer               string
	Maintainer_email         string
	Name                     string
	Project_urls             ProjectUrls
}

type ProjectUrls struct {
	Documentation string
	Funding       string
	Homepage      string
	Source        string
	Tracker       string
}

var packageRgxp = regexp.MustCompile("(?P<package>[a-zA-Z-_]+)(?P<versionSpec>.*)")
var httpClient = &http.Client{Timeout: 10 * time.Second}

const pypiUrl = "https://pypi.org/pypi/%v/json"

func Scan(files []string) string {
	message := fmt.Sprintf("Scanning %v\n", files)
	fmt.Print(message)

	allPackages := []string{}

	for _, file := range files {
		allPackages = append(allPackages, scanFile(file)...)
	}

	for _, pkg := range allPackages {
		getLicenseFromPypi(pkg)
	}

	return fmt.Sprintf("Found packages: %v\n", allPackages)
}

// Return a list of package names from a single file
func scanFile(file string) []string {
	f, err := os.Open(file)
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close()

	packages := []string{}

	scanner := bufio.NewScanner(f)

	for scanner.Scan() {
		line := scanner.Text()
		if packageRgxp.MatchString(line) {
			matches := packageRgxp.FindStringSubmatch(line)
			packageIdx := packageRgxp.SubexpIndex("package")
			packageName := matches[packageIdx]
			packages = append(packages, packageName)
		}

	}
	return packages
}

func getLicenseFromPypi(packageName string) {
	url := fmt.Sprintf(pypiUrl, packageName)
	resp, err := httpClient.Get(url)
	if err != nil {
		log.Fatal(err)
	}
	defer resp.Body.Close()

	var packageMeta PyPiPackageMeta

	json.NewDecoder(resp.Body).Decode(&packageMeta)
	// fmt.Printf("\ndata=%v", packageMeta)
	lic := packageMeta.Info.License
	fmt.Printf("package: %v license: %v\n", packageName, lic)
}
