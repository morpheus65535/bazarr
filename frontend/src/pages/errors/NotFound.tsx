import { FunctionComponent } from "react";
import { Box, Center, Container, Text, Title } from "@mantine/core";
import { faEyeSlash as fasEyeSlash } from "@fortawesome/free-regular-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

const NotFound: FunctionComponent = () => {
  return (
    <Container my="lg">
      <Center>
        <Title order={1}>
          <Box component="span" mr="md">
            <FontAwesomeIcon icon={fasEyeSlash}></FontAwesomeIcon>
          </Box>
          404
        </Title>
      </Center>
      <Center>
        <Text>The Request URL No Found</Text>
      </Center>
    </Container>
  );
};

export default NotFound;
