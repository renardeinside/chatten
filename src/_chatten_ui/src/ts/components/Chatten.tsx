import React from 'react';
import {DashComponentProps} from '../props';
import ChatUI from '../blocks/Chat';

type Props = {
    // Insert props
} & DashComponentProps;

/**
 * Component description
 */
const Chatten = (props: Props) => {
    const { id } = props;
    return (
        <div id={id}>
            <ChatUI />
        </div>
    )
}

Chatten.defaultProps = {};

export default Chatten;
