import unittest

from PyQt5.QtWidgets import QApplication
from SILA_Box import SILABox


class TestSILABox(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])

    def setUp(self):
        self.sila_box = SILABox()

    def tearDown(self):
        self.sila_box.close()


if __name__ == '__main__':
    unittest.main()


def test_launch_program_button(self):
    # Create a mock for os.system
    with unittest.mock.patch('os.system') as mock_system:
        # Set up the mock to return 0 (success)
        mock_system.return_value = 0

        # Create an instance of SILABox
        sila_box = SILABox()

        # Find the button for a specific program (e.g., "SILA VST Backup")
        for button in sila_box.findChildren(QPushButton):
            if button.text().strip() == "SILA VST Backup":
                target_button = button
                break

        # Simulate clicking the button
        QTest.mouseClick(target_button, Qt.LeftButton)

        # Check if os.system was called with the correct command
        mock_system.assert_called_once_with("start SILAVSTBackup.exe")

        # Check if the success message was shown
        self.assertTrue(hasattr(sila_box, 'msg_box'))
        self.assertEqual(sila_box.msg_box.windowTitle(), "Success")
        self.assertEqual(sila_box.msg_box.text(),
                         "Program launched successfully!")


def test_not_admin_exit(self, mocker):
    # Mock the is_admin method to return False
    mocker.patch.object(SILABox, 'is_admin', return_value=False)

    # Mock QMessageBox.critical to avoid actual message box display
    mock_critical = mocker.patch('PyQt5.QtWidgets.QMessageBox.critical')

    # Mock sys.exit to avoid actual program termination
    mock_exit = mocker.patch('sys.exit')

    # Create an instance of SILABox
    sila_box = SILABox()

    # Assert that QMessageBox.critical was called with the correct arguments
    mock_critical.assert_called_once_with(
        sila_box, "Error", "Este programa debe ejecutarse como administrador.")

    # Assert that sys.exit was called
    mock_exit.assert_called_once()


def test_launch_as_admin(self):
    with unittest.mock.patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=True):
        sila_box = SILABox()
        self.assertIsInstance(sila_box, SILABox)
        self.assertTrue(hasattr(sila_box, 'setup_ui'))
        self.assertTrue(hasattr(sila_box, 'create_appdata_directory'))


def test_create_appdata_directory(self):
    # Mock os.makedirs to track if it's called
    with unittest.mock.patch('os.makedirs') as mock_makedirs:
        # Create an instance of SILABox
        sila_box = SILABox()

        # Check if os.makedirs was called with the correct arguments
        mock_makedirs.assert_called_once_with(
            SILABox.APPDATA_DIR, exist_ok=True)


def test_program_buttons_display(self):
    self.sila_box.setup_ui()
    program_buttons = self.sila_box.findChildren(QPushButton)

    for i, program in enumerate(self.sila_box.PROGRAMS):
        # +1 to skip the "Install Audacity" button
        button = program_buttons[i + 1]
        self.assertEqual(button.text().strip(), program["name"])

        icon_path = self.sila_box.resource_path(program["icon"])
        if os.path.exists(icon_path):
            self.assertIsNotNone(button.icon())
        else:
            self.assertEqual(button.icon().isNull(), True)

    self.assertEqual(len(program_buttons) - 1, len(self.sila_box.PROGRAMS))


def test_launch_program_failure(self):
    self.sila_box.show_message = MagicMock()
    self.sila_box.launch_program("invalid_command")
    self.sila_box.show_message.assert_called_with(
        "Launch Error", "Failed to launch the program:\ninvalid_command")


def test_install_audacity_not_found(self):
    self.sila_box.resource_path = lambda x: "non_existent_path"
    with unittest.mock.patch.object(QMessageBox, 'exec_') as mock_exec:
        self.sila_box.install_program("audacity-win-3.7.1-64bit.exe")
        mock_exec.assert_called_once()
        self.assertEqual(
            mock_exec.call_args[0][0].windowTitle(), "File Not Found")
        self.assertEqual(mock_exec.call_args[0][0].text(
        ), "Installer not found: audacity-win-3.7.1-64bit.exe")


def test_install_audacity_button(self):
    # Create a mock for os.startfile and QMessageBox
    with patch('os.startfile') as mock_startfile, \
            patch('PyQt5.QtWidgets.QMessageBox.information') as mock_message_box:

        # Create an instance of SILABox
        sila_box = SILABox()

        # Find the "Install Audacity" button
        install_buttons = sila_box.findChildren(
            QPushButton, "Install Audacity")
        self.assertEqual(len(install_buttons), 1,
                         "Install Audacity button not found")
        install_button = install_buttons[0]

        # Simulate clicking the button
        QTest.mouseClick(install_button, Qt.LeftButton)

        # Check if os.startfile was called with the correct installer path
        expected_path = sila_box.resource_path("audacity-win-3.7.1-64bit.exe")
        mock_startfile.assert_called_once_with(expected_path)

        # Check if the success message was displayed
        mock_message_box.assert_called_once_with(
            sila_box,
            "Installation",
            "audacity-win-3.7.1-64bit.exe installation started."
        )


def test_set_background_image(self):
    self.sila_box.set_background_image()

    # Check if the palette has been set
    self.assertIsNotNone(self.sila_box.palette())

    # Check if the background brush is set in the palette
    brush = self.sila_box.palette().brush(QPalette.Window)
    self.assertIsNotNone(brush)

    # Check if the brush contains a pixmap
    self.assertTrue(brush.texture().isNull() == False)

    # Verify the pixmap's size (assuming BGSILABox.png is 810x670)
    self.assertEqual(brush.texture().size(), QSize(810, 670))


def test_install_audacity_not_found(self):
    self.sila_box.resource_path = lambda x: "non_existent_path"
    with unittest.mock.patch.object(QMessageBox, 'exec_') as mock_exec:
        self.sila_box.install_program("audacity-win-3.7.1-64bit.exe")
        mock_exec.assert_called_once()
        self.assertEqual(
            mock_exec.call_args[0][0].windowTitle(), "File Not Found")
        self.assertEqual(mock_exec.call_args[0][0].text(
        ), "Installer not found: audacity-win-3.7.1-64bit.exe")


def test_developer_info_display(self):
    dev_info = self.sila_box.create_developer_info()
    self.assertIsInstance(dev_info, QLabel)
    self.assertEqual(
        dev_info.text(), "Dev. Iván Ayub | sellocasadenubes@gmail.com")
    self.assertEqual(dev_info.font().family(), 'Arial')
    self.assertEqual(dev_info.font().pointSize(), 16)
    self.assertEqual(dev_info.styleSheet(),
                     "color: #FFD700; margin-top: 20px;")
    self.assertEqual(dev_info.alignment(), Qt.AlignCenter)
