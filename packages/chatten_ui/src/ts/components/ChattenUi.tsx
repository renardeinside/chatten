import React from 'react';
import {DashComponentProps} from '../props';
import ChatUI from '../blocks/Chat';
type Props = {
    // Insert props
} & DashComponentProps;

/**
 * Component description
 */
const ChattenUi = (props: Props) => {
    const { id } = props;
    return (
        <div id={id}>
            <ChatUI />
        </div>
    )
}

ChattenUi.defaultProps = {};

export default ChattenUi;
