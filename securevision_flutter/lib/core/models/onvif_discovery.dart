class OnvifDiscoveryRequest {
  const OnvifDiscoveryRequest({
    this.host,
    this.port = 80,
    this.username,
    this.password,
    this.timeoutSeconds = 5,
    this.profiles,
  });

  final String? host;
  final int port;
  final String? username;
  final String? password;
  final int timeoutSeconds;
  final List<String>? profiles;

  Map<String, dynamic> toJson() {
    return {
      if (host != null && host!.isNotEmpty) 'host': host,
      'port': port,
      if (username != null && username!.isNotEmpty) 'username': username,
      if (password != null && password!.isNotEmpty) 'password': password,
      'timeout': timeoutSeconds,
      if (profiles != null && profiles!.isNotEmpty) 'profiles': profiles,
    };
  }
}

class OnvifDiscoveryResult {
  const OnvifDiscoveryResult({
    required this.host,
    required this.profiles,
  });

  final String host;
  final List<OnvifProfile> profiles;

  factory OnvifDiscoveryResult.fromJson(Map<String, dynamic> json) {
    final rawProfiles = json['profiles'];
    final profiles = rawProfiles is List
        ? rawProfiles
            .whereType<Map>()
            .map((profile) => OnvifProfile.fromJson(
                  Map<String, dynamic>.from(profile),
                ))
            .toList()
        : <OnvifProfile>[];
    return OnvifDiscoveryResult(
      host: json['host'] as String? ?? 'unknown',
      profiles: profiles,
    );
  }
}

class OnvifProfile {
  const OnvifProfile({
    required this.name,
    required this.token,
    required this.uri,
  });

  final String name;
  final String token;
  final String uri;

  factory OnvifProfile.fromJson(Map<String, dynamic> json) {
    return OnvifProfile(
      name: json['name'] as String? ?? 'Profile',
      token: json['token'] as String? ?? '',
      uri: json['uri'] as String? ?? '',
    );
  }
}
