pluginManagement {
    repositories {
        maven { url = uri("https://redirector.gvt1.com/edgedl/android/maven2/") }
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        maven { url = uri("https://redirector.gvt1.com/edgedl/android/maven2/") }
        google()
        mavenCentral()
    }
}
rootProject.name="FreeNetHub"
include(":app")
// Private, separately installed VPN proof; the accepted :app remains fail-closed.
include(":vpnPrototype")
