from app.engine.mdtree import ImageSearch


# @patch('app.mdtree.requests.post')
# @patch('app.mdtree.Image.open')
# @patch('app.mdtree.requests.get')
def test_generate_image():
    # mock_requests_post.return_value.status_code = 200
    # mock_requests_post.return_value.json.return_value = [
    #     {
    #         "url": "http://example.com/image.png"
    #     }
    # ]
    # mock_requests_get.return_value.content = b'fake image content'
    # mock_image_open.return_value.__enter__.return_value = mock_image_open
    # mock_image_open.thumbnail.return_value = None
    # mock_image_open.save.return_value = None

    temp_folder_path = 'temp_images'
    own_domain = 'https://583b-35-184-213-130.ngrok-free.app/'

    image_search = ImageSearch
    image_path = image_search.generate_image('prompt', temp_folder_path, own_domain)
    print(image_path)
    # self.assertIsNotNone(image_path)
    # self.assertTrue(mock_requests_post.called)
    # self.assertTrue(mock_requests_get.called)
    # self.assertTrue(mock_image_open.thumbnail.called)
    # self.assertTrue(mock_image_open.save.called)


if __name__ == '__main__':
    test_generate_image()
