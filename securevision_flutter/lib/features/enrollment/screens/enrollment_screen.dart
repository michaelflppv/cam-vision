import 'package:flutter/material.dart';
import 'package:securevision_flutter/features/enrollment/screens/face_enrollment_screen.dart';
import 'package:securevision_flutter/features/enrollment/screens/plate_list_screen.dart';

class EnrollmentScreen extends StatelessWidget {
  const EnrollmentScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Enrollment'),
          bottom: const TabBar(
            tabs: [
              Tab(text: 'Faces'),
              Tab(text: 'Plates'),
            ],
          ),
        ),
        body: const TabBarView(
          children: [
            FaceEnrollmentScreen(),
            PlateListScreen(),
          ],
        ),
      ),
    );
  }
}
